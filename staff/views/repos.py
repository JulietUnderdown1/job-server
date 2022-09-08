from datetime import timedelta
from urllib.parse import quote, unquote

import structlog
from django.db.models import Count, Min
from django.db.models.functions import Least, Lower
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import View
from first import first
from furl import furl

from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role
from jobserver.github import _get_github_api
from jobserver.models import Job, User, Workspace


logger = structlog.get_logger(__name__)


def ran_at(job):
    return job.started_at or job.created_at


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class RepoDetail(View):
    get_github_api = staticmethod(_get_github_api)

    def get(self, request, *args, **kwargs):
        url = unquote(self.kwargs["repo_url"])

        org, name = furl(url).path.segments
        repo = self.get_github_api().get_repo(org, name)

        workspaces = (
            Workspace.objects.filter(repo=url)
            .select_related("created_by", "project", "project__org")
            .order_by("name")
        )
        users = User.objects.filter(job_requests__workspace__in=workspaces).distinct()

        jobs = Job.objects.filter(job_request__workspace__in=workspaces).annotate(
            first_run=Min(Least("started_at", "created_at"))
        )
        first_job_ran_at = ran_at(jobs.order_by("first_run").first())
        last_job_ran_at = ran_at(jobs.order_by("-first_run").first())

        twelve_month_limit = first_job_ran_at + timedelta(days=365)

        def build_workspace(workspace, all_users):
            """
            Build a dictionary representation of the Workspace data for the template

            We want to show a list of users-who-created-jobs-in-this-workspace
            in the template.  Getting this as part of the Workspace QuerySet
            doesn't appear to be possible (we tried Subquery and Prefetch to no
            avail).  Instead we've looked up the users who created jobs for
            each workspace used in this view and are pairing them up here.
            """

            # get the users who created jobs in this workspace or created it,
            # just in case the creator has not run any jobs.
            users = list(
                all_users.filter(job_requests__workspace=workspace)
                .distinct()
                .order_by(Lower("username"), Lower("fullname"))
            )
            if workspace.created_by not in users:
                users = [workspace.created_by, *users]

            return {
                "created_by": workspace.created_by,
                "get_staff_url": workspace.get_staff_url,
                "is_archived": workspace.is_archived,
                "job_requesting_users": users,
                "name": workspace.name,
            }

        workspaces = [build_workspace(w, users) for w in workspaces]

        context = {
            "first_job_ran_at": first_job_ran_at,
            "has_releases": "github-releases" in repo["topics"],
            "last_job_ran_at": last_job_ran_at,
            "repo": repo,
            "repo_url": url,
            "twelve_month_limit": twelve_month_limit,
            "workspaces": workspaces,
        }

        return TemplateResponse(
            request,
            "staff/repo_detail.html",
            context=context,
        )


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class RepoList(View):
    get_github_api = staticmethod(_get_github_api)

    def get(self, request, *args, **kwargs):
        """
        List private repos which are in need of converting to public

        Repos should be:
         * Private
         * not have `non-research` topic
         * first job was run > 11 months ago
        """
        all_repos = list(self.get_github_api().get_repos_with_dates("opensafely"))

        # remove repos with the non-research topic
        all_repos = [r for r in all_repos if "non-research" not in r["topics"]]

        private_repos = [repo for repo in all_repos if repo["is_private"]]

        all_workspaces = list(
            Workspace.objects.exclude(project__slug="opensafely-testing")
            .select_related("created_by", "project")
            .annotate(num_jobs=Count("job_requests__jobs"))
            .annotate(
                first_run=Min(
                    Least(
                        "job_requests__jobs__started_at",
                        "job_requests__jobs__created_at",
                    )
                ),
            )
        )

        def enhance(repo):
            """
            Enhance the repo dict from get_repos_with_dates() with workspace data

            We need to filter repos, not workspaces, so this gives us all the
            information we need when filtering further down.
            """
            # get workspaces just for this repo
            workspaces = [
                w for w in all_workspaces if repo["url"].lower() == w.repo.lower()
            ]
            workspaces = sorted(workspaces, key=lambda w: w.name.lower())

            # get workspaces which have run jobs
            with_jobs = [w for w in workspaces if w.first_run]

            # sorting by a datetime puts the workspaces into oldest job first
            with_jobs = sorted(with_jobs, key=lambda w: w.first_run)

            # get the first workspace to have run a job
            workspace = first(with_jobs, key=lambda w: w.first_run)

            # get first_run as either None or a datetime
            first_run = workspace.first_run if workspace else None

            # has this repo ever had jobs run with it?
            has_jobs = sum(w.num_jobs for w in workspaces) > 0

            return repo | {
                "first_run": first_run,
                "has_jobs": has_jobs,
                "has_releases": "github-releases" in repo["topics"],
                "quoted_url": quote(repo["url"], safe=""),
                "workspace": workspace,
                "workspaces": workspaces,
            }

        # add workspace (and related object) data to repos
        repos = [enhance(r) for r in private_repos]

        eleven_months_ago = timezone.now() - timedelta(days=30 * 11)

        def select(repo):
            """
            Select a repo based on various predicates below.

            We're already working with private repos here so we check

            * Has jobs or a workspace
            * First job to run happened over 11 months ago
            """
            if not (repo["workspaces"] and repo["has_jobs"]):
                logger.info("No workspaces/jobs", url=repo["url"])
                return False

            # because we know we have at least one job and first_run looks at
            # either started_at OR created_at we know we will always have a
            # value for first_run at this point
            first_ran_over_11_months_ago = repo["first_run"] < eleven_months_ago
            if not first_ran_over_11_months_ago:
                logger.info("First run <11mo ago", url=repo["url"])
                return False

            return True

        # select only repos we care about
        repos = [r for r in repos if select(r)]

        return TemplateResponse(request, "staff/repo_list.html", {"repos": repos})
