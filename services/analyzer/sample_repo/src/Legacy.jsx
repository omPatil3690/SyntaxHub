import ReactDOM from "react-dom";
import App from "./App";

class Legacy extends React.Component {
  componentWillMount() {
    console.log("about to mount");
  }
  render() {
    return <div ref="rootDiv">{this.props.children}</div>;
  }
}

ReactDOM.render(<App />, document.getElementById("root"));
