'use strict';

const e = React.createElement;

function ListItem(props) {

    const [visibility, setVisibility] = React.useState(false)

    return <li><div class="list-item" onClick={() => setVisibility(!visibility)}><p class="key-name">{props.keyName}</p><p class="key-value" style={{display: visibility ? 'block': 'none'}}>{props.value}</p></div></li>;
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
      displayList = <h4>There aren't any keys stored in the memcached database. Add keys by connecting to the memcached server on port 11211 and using the set command.</h4>
    }


    return (
      <div>{displayList}</div>
    );
  }
}

const domContainer = document.querySelector('#react-component');
ReactDOM.render(<KeyList keyList={keyValuePairs}/>, domContainer);
