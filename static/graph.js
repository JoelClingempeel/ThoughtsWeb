var data = {
    nodes: new vis.DataSet([]),
    edges: new vis.DataSet([])
};
var network = new vis.Network(document.getElementById('mynetwork'), data, {});
var selectedNode = ''
var selectedEdge = ''
const url = 'http://' + window.location.href.split('/')[2] + '/'

async function call_api(query_type, query_data) {
  let myData;
  const response = await fetch(url + query_type, {
    method: 'post',
    body: JSON.stringify(query_data),
    headers: new Headers({
      'content-type': 'application/json'
    })
  }).then(
    response => response.text()
  ).then(
    data => {myData = JSON.parse(data);}
  );
  return myData;
}

network.on('click', function(params) {
    if(params['nodes'].length > 0) {
      selectedNode = params['nodes'][0]
    } else {
      selectedNode = ''
    }
    if(params['edges'].length > 0){
      selectedEdge = params['edges']
    } else {
      selectedEdge = ''
    }
});

function add_node() {
    var node = prompt('Please enter a label for your new node.', 'Label goes here.');
    if(!network.body.data.nodes.get(node)) {
        network.body.data.nodes.add([{ id: node, label: node }]);
     }
     call_api('add_node', { label: node })
}

function remove_node() {
    if (selectedNode == '') {
            return;
    }
    network.body.data.nodes.remove(selectedNode);
    call_api('remove_node', { label: selectedNode });
}

function add_edge() {
    var node1 = prompt('Please enter first node.');
    var node2 = prompt('Please enter second node.');
    var edge_label = prompt('Please enter edge label.');
    if(!network.body.data.edges.get(node1 + '/' + node2) &&
       !network.body.data.edges.get(node2 + '/' + node1)) {
       network.body.data.edges.add([{ from: node1, to: node2, id: node1 + '/' + node2, label: edge_label }]);
       call_api('add_edge', { source: node1, sink: node2, label: edge_label })
    }
}

function remove_edge() {
    if (selectedEdge == '') {
            return;
    }
    network.body.data.edges.remove(selectedEdge);
    pair = String(selectedEdge).split('/')
    call_api('remove_edge', { source: pair[0], sink: pair[1] })
}

async function get_start() {
    let data = await call_api('graph_snapshot', '')
    for (i = 0; i < data['nodes'].length; i++) {
        node = data['nodes'][i]
        network.body.data.nodes.add([{ id: node, label: node }]);
    }
    for (j = 0; j < data['edges'].length; j++) {
        edge = data['edges'][j]
        network.body.data.edges.add([{ from: edge[0], to: edge[1], id: edge[0] + '/' + edge[1], label: edge[2] }]);
    }
}

get_start();
