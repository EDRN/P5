let dx=20;
let dy=200;
let margin = ({top: 10, right: 120, bottom: 10, left: 40})
let width  = 500;
let tree = d3.tree().nodeSize([dx, dy]);
let diagonal = d3.linkHorizontal().x(d => d.y).y(d => d.x);
let infobox=null;


function updatecollapsedlook(event,d) {
    let id=d.id;
    if (d._children) {
        if (d.children) {
            d3.select('#node_circle_'+id).attr('stroke-width',0);
        } else {
            d3.select('#node_circle_'+id).attr('stroke-width',0.5);
        }
    }
}

function reveal(e,d) {
    infobox.html(d.data.info);
    // Sorry Santiago: this doesn't work:
    //        .style('left',e.clientX-24)
    //        .style('top' ,e.clientY+24);
    infobox.style('left', (e.clientX - 24) + "px");
    infobox.style('top',  (e.clientY + 24) + "px");
    infobox.style('visibility','visible');
    let i=d.id;
    d3.select('#node_circle_'+i).style('fill','black');
}

function unreveal(e,d) {
    infobox.style('visibility','hidden');
    let i=d.id;
    d3.select('#node_circle_'+i).style("fill", d => d._children ? "#20a0f0": "#a0b0e0")
}

function makeSimpleHorizontalTree(flattree) {
      const root = d3.stratify().id(d=>d.name).parentId(d=>d.parent)(flattree);
      root.x0 = dy / 2;
      root.y0 = 0;
      root.descendants().forEach((d, i) => {
        d.id = i;
        d._children = d.children;
        if (d.depth && opennodelist.indexOf(d.data.name)<0) {
            d.children = null;
            updatecollapsedlook(null,d);
        }
      });

      const svg=d3.select('#canvas').append('svg')
          .attr("viewBox", [-margin.left, -margin.top, width, dx])
          .style("font", "8px Roboto")
          .style("fill", "#204040")
          .style("user-select", "none");

      const gLink = svg.append("g")
          .attr("fill", "none")
          .attr("stroke", "#555")
          .attr("stroke-opacity", 0.4)
          .attr("stroke-width", 1.5);

      const gNode = svg.append("g")
          .attr("pointer-events", "all");

      function update(source) {
        const duration = d3.event && d3.event.altKey ? 2500 : 250;
        const nodes = root.descendants().reverse();
        const links = root.links();

        // Compute the new tree layout.
        tree(root);

        let left = root;
        let right = root;
        root.eachBefore(node => {
          if (node.x < left.x) left = node;
          if (node.x > right.x) right = node;
        });

        const height = right.x - left.x + margin.top + margin.bottom;

        const transition = svg.transition()
            .duration(duration)
            .attr("viewBox", [-margin.left, left.x - margin.top, width, height])
            .tween("resize", window.ResizeObserver ? null : () => () => svg.dispatch("toggle"));

        // Update the nodes…
        const node = gNode.selectAll("g")
          .data(nodes, d => d.id);

        // Enter any new nodes at the parent's previous position.
        const nodeEnter = node.enter().append("g")
            .attr("transform", d => `translate(${source.y0},${source.x0})`)
            .attr("fill-opacity", 0)
            .attr("stroke-opacity", 0)
            .attr("cursor", d => d._children ? "pointer":"arrow")
            .on("click", (event, d) => {
              d.children = d.children ? null : d._children;
              update(d);
              updatecollapsedlook(event,d);
            });

        nodeEnter.append("circle")
            .attr("r", 2.5)
            .attr("fill", d => d._children ? "#20a0f0": "#a0b0e0")
            .attr("stroke-width", d => d._children ? (d.children?0:0.5) : 0)
            .attr("stroke", "black" )
            .attr("id", d => "node_circle_"+d.id )
            .on('mouseover',(e,d)=>reveal(e,d))
            .on('mouseout' ,(e,d)=>unreveal(e,d))
            ;

        nodeEnter.append("text")
            .attr("class","nodelabel")
            .attr("dy", "0.31em")
            .attr("x", d => d._children ? -6 : 6)
            .attr("text-anchor", d => d._children ? "end" : "start")
            .text(d => d.data.name)
            .on('mouseover',(e,d)=>reveal(e,d))
            .on('mouseout' ,(e,d)=>unreveal(e,d))
            .attr("id", d => "node_label_"+d.id )
          .clone(true).lower()
            .attr("stroke-linejoin", "round")
            .attr("stroke-width", 3)
            .attr("stroke", "white");

        // Transition nodes to their new position.
        const nodeUpdate = node.merge(nodeEnter).transition(transition)
            .attr("transform", d => `translate(${d.y},${d.x})`)
            .attr("fill-opacity", 1)
            .attr("stroke-opacity", 1);

        // Transition exiting nodes to the parent's new position.
        const nodeExit = node.exit().transition(transition).remove()
            .attr("transform", d => `translate(${source.y},${source.x})`)
            .attr("fill-opacity", 0)
            .attr("stroke-opacity", 0);

        // Update the links…
        const link = gLink.selectAll("path")
          .data(links, d => d.target.id);

        // Enter any new links at the parent's previous position.
        const linkEnter = link.enter().append("path")
            .attr("d", d => {
              const o = {x: source.x0, y: source.y0};
              return diagonal({source: o, target: o});
            });

        // Transition links to their new position.
        link.merge(linkEnter).transition(transition)
            .attr("d", diagonal);

        // Transition exiting nodes to the parent's new position.
        link.exit().transition(transition).remove()
            .attr("d", d => {
              const o = {x: source.x, y: source.y};
              return diagonal({source: o, target: o});
            });

        // Stash the old positions for transition.
        root.eachBefore(d => {
          d.x0 = d.x;
          d.y0 = d.y;
        });
      }

      update(root);

      return svg.node();
}

function aggregateJPLTree() {
    for (let i in flattree) {
        let info="<div class=nodeid>["+i+"]</div>";
        let p=flattree[i].parent;
        let parents="";
        while (p!="") {
            let pi=-1;
            for (let index in flattree) if (flattree[index].name==p) pi=index;
            if (pi>=0) {
               parents="<div class=nodeparent>"+flattree[pi].name+"</div>"+parents;
               p=flattree[pi].parent;
            } else p="";
        }
        info+=parents;
        info+="<div class=nodename>"+flattree[i].name+"</div>";
        for (let j in flattree) {
            if (flattree[j].parent==flattree[i].name)
                info+="<div class=nodechild>"+flattree[j].name+"</div>";
        }
        flattree[i]['info']=info;
    }
}
function taxonomy_main() {
     infobox=d3.select('.infobox').style('visibility','hidden');
     aggregateJPLTree();
     makeSimpleHorizontalTree(flattree);
}
