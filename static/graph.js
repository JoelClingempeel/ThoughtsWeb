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

async function update_display_text(note_label) {
    if (note_label == '') {
        document.getElementById('paragraph_display').innerHTML = '';
    } else {
        let display_text = await call_api('get_note', { node: note_label });
        document.getElementById('paragraph_display').innerHTML = display_text['note'];
    }
}

network.on('click', function(params) {
    if(params['nodes'].length > 0) {
      selectedNode = params['nodes'][0]
    } else {
      selectedNode = ''
    }
    update_display_text(selectedNode)
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
     call_api('add_node', { label: node, type: 'entity' })
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
       call_api('add_edge', { source: node1, sink: node2, label: edge_label, type: 'semantic' })
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

function add_note() {
    if (selectedNode == '') {
            return;
    }
    var note = prompt('Please enter a name for your note.');
    network.body.data.nodes.add([{ id: note, label: note, color: 'red'}]);
    call_api('add_node', { label: note, type: 'note'  })
    network.body.data.edges.add([{ from: note, to: selectedNode, id: note + '/' + selectedNode, label: '--->' }]);
    call_api('add_edge', { source: note, sink: selectedNode, label: '--->', type: 'note' })
    update_display_text(note)
}

function add_parent_child() {
    var parent = prompt('Please enter parent node.');
    var child = prompt('Please enter node node.');
    if(!network.body.data.edges.get(child + '/' + parent) &&
       !network.body.data.edges.get(parent + '/' + child)) {
       network.body.data.edges.add([{ from: child, to: parent, id: child + '/' + parent, label: '--->' }]);
       call_api('add_edge', { source: child, sink: parent, label: '--->', type: 'hierarchical' })
    }
}

async function initialize() {
    let data = await call_api('graph_snapshot', '')
    for (i = 0; i < data['nodes'].length; i++) {
        node = data['nodes'][i]
        if (node[1] == 'entity') {
            network.body.data.nodes.add([{ id: node[0], label: node[0] }]);
        } else {
            network.body.data.nodes.add([{ id: node[0], label: node[0], color: 'red' }]);
        }
    }
    for (j = 0; j < data['edges'].length; j++) {
        edge = data['edges'][j]
        network.body.data.edges.add([{ from: edge[0], to: edge[1], id: edge[0] + '/' + edge[1], label: edge[2] }]);
    }
}

function clear_graph() {
    data = {
        nodes: new vis.DataSet([]),
        edges: new vis.DataSet([])
    };
    network = new vis.Network(document.getElementById('mynetwork'), data, {});
    selectedNode = ''
    selectedEdge = ''
}

async function show_only_children() {
    let data = await call_api('get_children', { root: selectedNode })
    clear_graph();
    for (i = 0; i < data['nodes'].length; i++) {
        node = data['nodes'][i]
        if (node[1] == 'entity') {
            network.body.data.nodes.add([{ id: node[0], label: node[0] }]);
        } else {
            network.body.data.nodes.add([{ id: node[0], label: node[0], color: 'red' }]);
        }
    }
    for (j = 0; j < data['edges'].length; j++) {
        edge = data['edges'][j]
        network.body.data.edges.add([{ from: edge[0], to: edge[1], id: edge[0] + '/' + edge[1], label: edge[2] }]);
    }
}

function restore_graph() {
    clear_graph();
    initialize();
}

initialize();
