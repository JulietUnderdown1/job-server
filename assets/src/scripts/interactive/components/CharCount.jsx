import { number } from "prop-types";
import React from "react";

function CharCount({ current, min, max }) {
  if (current === max) {
    return <p className="text-sm">No characters remaining</p>;
  }

  if (current < min) {
    return <p className="text-sm">{current - min} more characters required</p>;
  }

  if (current < max) {
    return <p className="text-sm">{max - current} characters remaining</p>;
  }
  return <p className="text-sm"> chars remaining</p>;
}

CharCount.defaultProps = {
  min: null,
  max: null,
};

CharCount.propTypes = {
  current: number.isRequired,
  min: number,
  max: number,
};

export default CharCount;
