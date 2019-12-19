'use strict';

const e = React.createElement;

function ListItem(props) {

    const [visibility, setVisibility] = React.useState(true)

    return <li><div><p onClick={() => setVisibility(!visibility)}>{props.keyName}: </p><p style={{display: visibility ? 'block': 'none'}}>{props.value}</p></div></li>;
}

class KeyList extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      keyList: props.keyList
    };
  }

  render() {
    let displayList
    if (this.state.keyList.length > 0) {
      displayList = <ul>
            {this.state.keyList.map((item) =>
              <ListItem
                key={item.keyName}
                keyName={item.keyName}
                value={item.value}
              />
            )}
      </ul>;
    } else {
      displayList = <p>There aren't any keys stored in the memcached database</p>
    }


    return (
      <div>{displayList}</div>
    );
  }
}

const domContainer = document.querySelector('#react-component');
ReactDOM.render(<KeyList keyList={keyValuePairs}/>, domContainer);
