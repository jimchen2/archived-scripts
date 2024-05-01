// DownloadButton.js

import PropTypes from "prop-types";
import React, { Component } from "react";
import classNames from "classnames";

export default class DownloadButton extends Component {
  constructor(props) {
    super(props);
    this.handleClick = this.handleClick.bind(this);
  }

  handleClick() {
    // You can add specific logic here for when the button is clicked
    console.log("Download button clicked");
  }

  render() {
    const { player, className } = this.props;
    const { currentSrc } = player;

    return (
      <a
        ref={(c) => {
          this.button = c;
        }}
        className={classNames(
          className,
          "video-react-control",
          "video-react-button"
        )}
        href={currentSrc}
        download
        style={{
          backgroundImage:
            "url(data:image/svg+xml;base64,PHN2ZyBmaWxsPSIjRkZGRkZGIiBoZWlnaHQ9IjE4IiB2aWV3Qm94PSIwIDAgMjQgMjQiIHdpZHRoPSIxOCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4gICAgPHBhdGggZD0iTTE5IDloLTRWM0g5djZINWw3IDcgNy03ek01IDE4djJoMTR2LTJINXoiLz4gICAgPHBhdGggZD0iTTAgMGgyNHYyNEgweiIgZmlsbD0ibm9uZSIvPjwvc3ZnPg==)",
          backgroundRepeat: "no-repeat",
          backgroundPosition: "center",
        }}
        tabIndex="0"
        onClick={this.handleClick}
      >
        {/* This is intentionally left blank to show the background image as the button */}
      </a>
    );
  }
}

DownloadButton.propTypes = {
  player: PropTypes.object,
  className: PropTypes.string,
};
