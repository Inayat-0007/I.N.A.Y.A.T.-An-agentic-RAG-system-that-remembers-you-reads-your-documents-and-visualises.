import json
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.graph_store import get_visualization_data


def generate_debug_html():
    graph_data = get_visualization_data()
    nodes_js = json.dumps(graph_data["nodes"])
    edges_js = json.dumps(graph_data["edges"])

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <style type="text/css">
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
            body {{
                margin: 0;
                padding: 0;
                background-color: #040408;
                font-family: 'Outfit', sans-serif;
                overflow: hidden;
            }}
            #container-split {{
                display: flex;
                flex-direction: row;
                width: 100%;
                height: 520px;
                background: #080810;
                border: 1px solid rgba(167, 139, 250, 0.15);
                border-radius: 16px;
                overflow: hidden;
                box-sizing: border-box;
            }}
            #mynetwork {{
                flex: 6.8;
                width: 68%;
                height: 100%;
            }}
            #detail-drawer {{
                flex: 3.2;
                width: 32%;
                height: 100%;
                background: rgba(13, 13, 23, 0.95);
                border-left: 1px solid rgba(167, 139, 250, 0.15);
                padding: 1.2rem;
                box-sizing: border-box;
                display: flex;
                flex-direction: column;
                color: #e4e4e7;
                overflow-y: auto;
                box-shadow: -5px 0 20px rgba(0,0,0,0.5);
            }}
            #drawer-header {{
                font-size: 1rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 1rem;
                padding-bottom: 0.5rem;
                border-bottom: 1px solid rgba(167, 139, 250, 0.2);
                background: linear-gradient(135deg, #c084fc, #818cf8);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            .drawer-section {{
                margin-bottom: 0.85rem;
            }}
            .section-label {{
                font-size: 0.72rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                color: #71717a;
                font-weight: 600;
                margin-bottom: 0.25rem;
            }}
            .section-val {{
                font-size: 0.88rem;
                color: #e4e4e7;
                font-weight: 400;
            }}
            .tag {{
                display: inline-block;
                padding: 0.2rem 0.6rem;
                border-radius: 6px;
                font-size: 0.72rem;
                font-weight: 600;
                text-transform: uppercase;
                margin-top: 0.35rem;
            }}
            .tag-agent {{ background: rgba(167, 139, 250, 0.15); color: #c084fc; border: 1px solid rgba(167, 139, 250, 0.3); }}
            .tag-llm {{ background: rgba(52, 211, 153, 0.15); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); }}
            .tag-memory {{ background: rgba(96, 165, 250, 0.15); color: #60a5fa; border: 1px solid rgba(96, 165, 250, 0.3); }}
            .tag-graph {{ background: rgba(251, 113, 133, 0.15); color: #fb7185; border: 1px solid rgba(251, 113, 133, 0.3); }}
            .tag-resilience {{ background: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); }}
            .tag-user {{ background: rgba(244, 114, 182, 0.15); color: #f472b6; border: 1px solid rgba(244, 114, 182, 0.3); }}
            .tag-chunk {{ background: rgba(148, 163, 184, 0.15); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.3); }}
            .tag-entity {{ background: rgba(129, 140, 248, 0.15); color: #a5b4fc; border: 1px solid rgba(129, 140, 248, 0.3); }}
            
            .prop-box {{
                background: rgba(15, 15, 24, 0.6);
                border: 1px solid rgba(63, 63, 80, 0.4);
                border-radius: 8px;
                padding: 0.6rem 0.8rem;
                font-size: 0.8rem;
                line-height: 1.4;
                color: #d4d4d8;
                max-height: 180px;
                overflow-y: auto;
                word-break: break-word;
            }}
            .use-btn {{
                background: linear-gradient(135deg, #c084fc 0%, #6366f1 100%);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0.55rem 1rem;
                font-size: 0.82rem;
                font-weight: 600;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 0.4rem;
                margin-top: 1rem;
                transition: all 0.25s ease;
                box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
            }}
            .use-btn:hover {{
                box-shadow: 0 6px 18px rgba(99, 102, 241, 0.5);
                transform: translateY(-1px);
            }}
            .use-btn:active {{
                transform: translateY(0);
            }}
            
            #toast {{
                visibility: hidden;
                min-width: 240px;
                background-color: #10b981;
                color: #fff;
                text-align: center;
                border-radius: 8px;
                padding: 0.65rem;
                position: fixed;
                z-index: 1000;
                bottom: 20px;
                right: 20px;
                font-size: 0.8rem;
                font-weight: 600;
                box-shadow: 0 4px 15px rgba(16, 185, 129, 0.45);
                opacity: 0;
                transition: opacity 0.3s, visibility 0.3s;
            }}
            #toast.show {{
                visibility: visible;
                opacity: 1;
            }}
        </style>
    </head>
    <body>
    <div id="container-split">
        <div id="mynetwork"></div>
        <div id="detail-drawer">
            <div id="drawer-header">Neural Details</div>
            <div id="drawer-body">
                <p style="color: #71717a; font-size: 0.85rem; font-style: italic; margin-top: 0;">Click on a node or connection path in the graph to view properties.</p>
            </div>
        </div>
    </div>
    <div id="toast">Prompt copied! Paste it in the chat box on the left.</div>

    <script type="text/javascript">
        window.onerror = function(message, source, lineno, colno, error) {{
            console.error("IFRAME ERROR: " + message + " at " + source + ":" + lineno + ":" + colno);
            return false;
        }};
        var nodes = new vis.DataSet({nodes_js});
        var edges = new vis.DataSet({edges_js});
        var container = document.getElementById('mynetwork');
        var data = {{
            nodes: nodes,
            edges: edges
        }};
        var options = {{
            nodes: {{
                shape: 'dot',
                size: 20,
                font: {{
                    color: '#ffffff',
                    size: 13,
                    face: 'Outfit, sans-serif'
                }},
                borderWidth: 2,
                shadow: true
            }},
            edges: {{
                width: 2,
                color: {{ color: 'rgba(129, 140, 248, 0.4)', highlight: '#c084fc' }},
                font: {{
                    color: '#a5b4fc',
                    size: 10,
                    align: 'horizontal',
                    background: '#040408'
                }},
                arrows: {{
                    to: {{ enabled: true, scaleFactor: 0.7 }}
                }},
                smooth: {{
                    type: 'cubicBezier',
                    forceDirection: 'none',
                    roundness: 0.4
                }}
            }},
            groups: {{
                Agent: {{ color: {{ background: '#c084fc', border: '#a78bfa' }} }},
                LLM: {{ color: {{ background: '#34d399', border: '#059669' }} }},
                Memory: {{ color: {{ background: '#60a5fa', border: '#2563eb' }} }},
                GraphStore: {{ color: {{ background: '#fb7185', border: '#e11d48' }} }},
                Resilience: {{ color: {{ background: '#fbbf24', border: '#d97706' }} }},
                User: {{ color: {{ background: '#f472b6', border: '#db2777' }} }},
                Entity: {{ color: {{ background: '#818cf8', border: '#6366f1' }} }},
                Chunk: {{ color: {{ background: '#94a3b8', border: '#475569' }} }}
            }},
            physics: {{
                stabilization: false,
                barnesHut: {{
                    gravitationalConstant: -3500,
                    springConstant: 0.04,
                    springLength: 120
                }}
            }},
            interaction: {{
                hover: true
            }}
        }};
        var network = new vis.Network(container, data, options);
        
        var drawerBody = document.getElementById('drawer-body');
        var drawerHeader = document.getElementById('drawer-header');
        
        function renderProperties(props) {{
            if (!props || Object.keys(props).length === 0) {{
                return '<p style="color: #71717a; font-style: italic; font-size: 0.8rem;">None</p>';
            }}
            var html = '<div style="display:flex; flex-direction:column; gap:0.45rem;">';
            for (var key in props) {{
                if (props.hasOwnProperty(key)) {{
                    html += '<div>';
                    html += '<div class="section-label">' + key + '</div>';
                    if (key === 'text') {{
                        html += '<div class="prop-box" style="white-space: pre-wrap;">' + props[key] + '</div>';
                    }} else {{
                        html += '<div class="section-val">' + props[key] + '</div>';
                    }}
                    html += '</div>';
                }}
            }}
            html += '</div>';
            return html;
        }}

        function getTagClass(group) {{
            var g = (group || '').toLowerCase();
            if (g.includes('agent')) return 'tag-agent';
            if (g.includes('llm')) return 'tag-llm';
            if (g.includes('memory')) return 'tag-memory';
            if (g.includes('graph')) return 'tag-graph';
            if (g.includes('resilience')) return 'tag-resilience';
            if (g.includes('user')) return 'tag-user';
            if (g.includes('chunk')) return 'tag-chunk';
            return 'tag-entity';
        }}
        
        function selectNodeHandler(nodeId) {{
            var node = nodes.get(nodeId);
            if (!node) return;
            
            drawerHeader.innerText = "Node Details";
            
            var tagClass = getTagClass(node.group);
            var labelName = node.label || 'Unnamed Node';
            var groupName = node.group || 'Entity';
            
            // Formulate prompt
            var promptText = "Tell me more about " + labelName;
            if (node.properties) {{
                if (node.properties.text) {{
                    promptText = "From the document chunk details, tell me more about: \\"" + node.properties.text.substring(0, 150).replace(/"/g, '\\"') + "...\\"";
                }} else if (node.properties.Description) {{
                    promptText = "Tell me about " + labelName + ": " + node.properties.Description;
                }}
            }}
            
            var html = '';
            html += '<div class="drawer-section">';
            html += '<div class="section-label">Node Name</div>';
            html += '<div class="section-val" style="font-weight:600; font-size:0.95rem;">' + labelName + '</div>';
            html += '<span class="tag ' + tagClass + '">' + groupName + '</span>';
            html += '</div>';
            
            html += '<div class="drawer-section">';
            html += '<div class="section-label">Attributes</div>';
            html += renderProperties(node.properties);
            html += '</div>';
            
            html += '<button class="use-btn" onclick="copyPrompt(\'' + btoa(unescape(encodeURIComponent(promptText))) + '\')">';
            html += '<span>Use in Chat 💬</span>';
            html += '</button>';
            
            drawerBody.innerHTML = html;
        }}
        
        function selectEdgeHandler(edgeId) {{
            var edge = edges.get(edgeId);
            if (!edge) return;
            
            drawerHeader.innerText = "Connection Details";
            
            var fromNode = nodes.get(edge.from);
            var toNode = nodes.get(edge.to);
            var fromName = fromNode ? fromNode.label : 'Node ' + edge.from;
            var toName = toNode ? toNode.label : 'Node ' + edge.to;
            
            var relType = edge.label || 'RELATED';
            var promptText = "Explain the connection: " + fromName + " —[" + relType + "]—> " + toName;
            if (edge.properties && Object.keys(edge.properties).length > 0) {{
                var propsStr = JSON.stringify(edge.properties);
                promptText += " with properties " + propsStr;
            }}
            
            var html = '';
            html += '<div class="drawer-section">';
            html += '<div class="section-label">Source Node</div>';
            html += '<div class="section-val" style="font-weight:600;">' + fromName + '</div>';
            html += '</div>';
            
            html += '<div class="drawer-section">';
            html += '<div class="section-label">Relationship Path</div>';
            html += '<div class="section-val" style="color:#c084fc; font-weight:600;">→ ' + relType + ' →</div>';
            html += '</div>';
            
            html += '<div class="drawer-section">';
            html += '<div class="section-label">Target Node</div>';
            html += '<div class="section-val" style="font-weight:600;">' + toName + '</div>';
            html += '</div>';
            
            html += '<div class="drawer-section">';
            html += '<div class="section-label">Attributes</div>';
            html += renderProperties(edge.properties);
            html += '</div>';
            
            html += '<button class="use-btn" onclick="copyPrompt(\'' + btoa(unescape(encodeURIComponent(promptText))) + '\')">';
            html += '<span>Use in Chat 💬</span>';
            html += '</button>';
            
            drawerBody.innerHTML = html;
        }}
        
        network.on("selectNode", function(params) {{
            if (params.nodes.length > 0) {{
                selectNodeHandler(params.nodes[0]);
            }}
        }});
        
        network.on("selectEdge", function(params) {{
            if (params.nodes.length === 0 && params.edges.length > 0) {{
                selectEdgeHandler(params.edges[0]);
            }}
        }});
        
        network.on("deselectNode", function(params) {{
            resetDrawer();
        }});
        
        network.on("deselectEdge", function(params) {{
            resetDrawer();
        }});
        
        function resetDrawer() {{
            drawerHeader.innerText = "Neural Details";
            drawerBody.innerHTML = '<p style="color: #71717a; font-size: 0.85rem; font-style: italic; margin-top: 0;">Click on a node or connection path in the graph to view properties.</p>';
        }}
        
        function copyPrompt(base64Text) {{
            var promptText = decodeURIComponent(escape(atob(base64Text)));
            navigator.clipboard.writeText(promptText).then(function() {{
                var toast = document.getElementById('toast');
                toast.className = 'show';
                setTimeout(function(){{ toast.className = toast.className.replace('show', ''); }}, 3000);
            }}, function(err) {{
                alert("Prompt generated: \\n\\n" + promptText + "\\n\\n(Clipboard access blocked, please copy manually)");
            }});
        }}
    </script>
    </body>
    </html>
    """

    os.makedirs(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "scratch"),
        exist_ok=True,
    )
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "scratch", "network.html"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Exported debug HTML to {out_path}")


if __name__ == "__main__":
    generate_debug_html()
