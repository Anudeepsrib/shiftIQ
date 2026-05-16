import React, { Component } from 'react';

class LegacyButton extends Component {
  render() {
    return <button>{this.props.label}</button>;
  }
}

export default LegacyButton;
