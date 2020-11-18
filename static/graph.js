const url = 'https://thoughtsweb.herokuapp.com/'

var data = {
    nodes: new vis.DataSet([]),
    edges: new vis.DataSet([])
};
var network = new vis.Network(document.getElementById('network_panel'), data, {});
var selectedNode = ''
var selectedEdge = ''
var node_list;

async function call_api(query_type, query_data) {
  let myData;
  const response = await fetch(url + query_type, {
    method: 'post',
    body: JSON.stringify(query_data),
    xhrFields: {withCredentials: true},
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

async function update_display_text(node) {
    if (node == '') {
        document.getElementById('privacy_display').innerHTML = '';
        document.getElementById('note_display').innerHTML = '';
        return;
    }

    let display_text = await call_api('get_node_data', { node: node });

    // For non-global nodes, get privacy status and number of notes owned by user.
    if (display_text['is_global'] == 'False') {
        // Privacy status.
        if (display_text['private'] == 'True') {
            document.getElementById('privacy_display').innerHTML = 'This node is currently <b>private</b>.  ' +
            '<button onclick="toggle_privacy();">Toggle Privacy</button>';
        } else {
            document.getElementById('privacy_display').innerHTML = 'This node is currently <b>public</b>.  ' +
            '<button onclick="toggle_privacy();">Toggle Privacy</button>';
        }

        // Note count.
        if (display_text['num_notes'] != '0' && display_text['note'] == '') {
            document.getElementById('note_count').innerHTML = 'Notes:  ' + display_text['num_notes'] +
            '<button onclick="show_notes();">Show Notes</button> <button onclick="hide_notes();">Hide Notes</button>';
        } else if (display_text['note'] == '') {
            document.getElementById('note_count').innerHTML = 'This node has no notes.';
        } else {
            document.getElementById('note_count').innerHTML = '';
        }
    }

    // For global nodes, get count of all notes.
    if (display_text['num_global_notes'] != '0') {
        document.getElementById('global_note_count').innerHTML = 'Global Notes:  ' + display_text['num_global_notes'] +
        '<button onclick="global_show_notes();">Show Global Notes</button>';
    } else if (display_text['note'] == '') {
        document.getElementById('global_note_count').innerHTML = 'This node has no global notes.';
    } else {
        document.getElementById('global_note_count').innerHTML = '';
    }

    // Show other users.
    var users_html = ''
    for (i = 0; i < display_text['other_users'].length; i++) {
        users_html += ('<a href="profile/' + display_text['other_users'][i] + '"> '
                       + display_text['other_users'][i] + ' </a><br/>')
    }
    document.getElementById('other_users').innerHTML = users_html;

    // Note display.
    document.getElementById('note_display').innerHTML = display_text['note'];
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


function restore_graph(data) {
    for (i = 0; i < data['nodes'].length; i++) {
        node = data['nodes'][i]
        if (network.body.data.nodes.get(node[0]) == null) {
            if (node[1] == 'entity') {
                network.body.data.nodes.add([{ id: node[0],
                                               label: node[0] }]);
            } else if (node[1] == 'global_entity') {
                network.body.data.nodes.add([{ id: node[0],
                                               label: node[0],
                                               color: 'green' }]);
            }
            else if (node[1] == 'global_note') {
                network.body.data.nodes.add([{ id: node[0],
                                               label: node[0],
                                               color: 'purple' }]);
            } else {
                network.body.data.nodes.add([{ id: node[0],
                                               label: node[0],
                                               color: 'red' }]);
            }
        }
    }
    for (j = 0; j < data['edges'].length; j++) {
        edge = data['edges'][j]
        if (network.body.data.edges.get(edge[0] + '/' + edge[1]) == null) {
            network.body.data.edges.add([{ from: edge[0],
                                           to: edge[1],
                                           id: edge[0] + '/' + edge[1],
                                           label: edge[2],
                                           arrows: 'to' }]);
         }
    }
}

async function initialize() {
    let data = await call_api('graph_snapshot', '')
    restore_graph(data)
    node_list = data['nodes']
}

function clear_graph() {
    for (i = 0; i < node_list.length; i++) {
        network.body.data.nodes.remove(node_list[i]);
    }
}

async function restrict_to_children() {
    let data = await call_api('get_children', { root: selectedNode })
    clear_graph();
    restore_graph(data);
}

function show_entire_graph() {
    clear_graph();
    initialize();
}

async function expand_node() {
    if (selectedNode == '') {
        return;
    }
    let data = await call_api('get_neighbors', { node: selectedNode });
    restore_graph(data);
}

async function global_expand_node() {
    if (selectedNode == '') {
        return;
    }
    let data = await call_api('get_global_neighbors', { node: selectedNode });
    restore_graph(data);
}

function hide_node() {
    if (selectedNode == '') {
        return;
    }
    network.body.data.nodes.remove(selectedNode);
}

async function show_notes() {
    if (selectedNode == '') {
        return;
    }
    let data = await call_api('get_notes', { node: selectedNode });
    restore_graph(data);
}

async function global_show_notes() {
    if (selectedNode == '') {
        return;
    }
    let data = await call_api('get_global_notes', { node: selectedNode });
    restore_graph(data);
}

async function hide_notes() {
    if (selectedNode == '') {
        return;
    }
    let data = await call_api('get_notes', { node: selectedNode });
    for (i = 0; i < data['nodes'].length; i++) {
        node = data['nodes'][i]
        network.body.data.nodes.remove([{ id: node[0],
                                          label: node[0] }]);

    }
    for (j = 0; j < data['edges'].length; j++) {
        edge = data['edges'][j]
        network.body.data.edges.remove([{ from: edge[0],
                                          to: edge[1],
                                          id: edge[0] + '/' + edge[1],
                                          label: edge[2],
                                          arrows: 'to' }]);
     }

}

function add_node() {
    var node = prompt('Please enter a label for your new node.', 'Label goes here.');
    if(!network.body.data.nodes.get(node)) {
        network.body.data.nodes.add([{ id: node,
                                       label: node }]);
     }
     call_api('add_node', { label: node,
                            type: 'entity' });
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
       network.body.data.edges.add([{ from: node1,
                                      to: node2,
                                      id: node1 + '/' + node2,
                                      label: edge_label,
                                      arrows: 'to' }]);
       call_api('add_edge', { source: node1,
                              sink: node2,
                              label: edge_label,
                              type: 'semantic' })
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
    network.body.data.nodes.add([{ id: note,
                                   label: note,
                                   color: 'red'}]);
    call_api('add_node', { label: note,
                           type: 'note'  })
    network.body.data.edges.add([{ from: note,
                                   to: selectedNode,
                                   id: note + '/' + selectedNode,
                                   label: '--->',
                                   arrows: 'to' }]);
    call_api('add_edge', { source: note,
                           sink: selectedNode,
                           label: '--->',
                           type: 'note' })
    update_display_text(note)
}

function add_parent_child() {
    var parent = prompt('Please enter parent node.');
    var child = prompt('Please enter node node.');
    if(!network.body.data.edges.get(child + '/' + parent) &&
       !network.body.data.edges.get(parent + '/' + child)) {
       network.body.data.edges.add([{ from: child,
                                      to: parent,
                                      id: child + '/' + parent,
                                      label: '--->',
                                      arrows: 'to' }]);
       call_api('add_edge', { source: child,
                              sink: parent,
                              label: '--->',
                              type: 'hierarchical' })
    }
}

async function search_for_nodes() {
    let query = document.getElementById('node_search').value;
    let data = await call_api('node_search', { query: query });
    restore_graph(data);
}

async function toggle_privacy() {
    await call_api('toggle_privacy', { node: selectedNode });
    update_display_text(selectedNode)
}

initialize();
