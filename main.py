from flask import Flask, render_template_string, request
from pyvis.network import Network
import networkx as nx
from typing import Tuple, Dict

app = Flask(__name__)

# Инициализация графа
G = nx.Graph()

# HTML шаблон с формой для добавления/удаления вершин и рёбер, поиска паросочетания и сброса цветов
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Graph Editor</title>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.bundle.min.js"></script>
    <style>
        .graph-container {
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container py-5">
        <h1 class="text-center mb-4">Graph Editor</h1>

        {% if not is_bipartite %}
            <div class="alert alert-danger text-center">The graph is not bipartite!</div>
        {% else %}
            <div class="alert alert-success text-center">The graph is bipartite!</div>
        {% endif %}

        {% if error is not none %}
            <div class="alert alert-danger text-center">{{ error }}</div>
        {% endif %}

        <div class="row justify-content-center">
            <div class="col-12 col-md-6 mb-3">
                <form class="form-inline justify-content-center" action="/add_node" method="post">
                    <input type="text" class="form-control mb-2 mr-sm-2" name="node" placeholder="Node Name">
                    <select name="color" class="form-control mb-2 mr-sm-2">
                        <option value="blue">Blue</option>
                        <option value="yellow">Yellow</option>
                    </select>
                    <button type="submit" class="btn btn-primary mb-2">Add Node</button>
                </form>
            </div>
            <div class="col-12 col-md-6 mb-3">
                <form class="form-inline justify-content-center" action="/add_edge" method="post">
                    <input type="text" class="form-control mb-2 mr-sm-2" name="node1" placeholder="Node 1">
                    <input type="text" class="form-control mb-2 mr-sm-2" name="node2" placeholder="Node 2">
                    <button type="submit" class="btn btn-primary mb-2">Add Edge</button>
                </form>
            </div>
            <div class="col-12 col-md-6 mb-3">
                <form class="form-inline justify-content-center" action="/remove_node" method="post">
                    <input type="text" class="form-control mb-2 mr-sm-2" name="node" placeholder="Node Name">
                    <button type="submit" class="btn btn-danger mb-2">Remove Node</button>
                </form>
            </div>
            <div class="col-12 col-md-6 mb-3">
                <form class="form-inline justify-content-center" action="/remove_edge" method="post">
                    <input type="text" class="form-control mb-2 mr-sm-2" name="node1" placeholder="Node 1">
                    <input type="text" class="form-control mb-2 mr-sm-2" name="node2" placeholder="Node 2">
                    <button type="submit" class="btn btn-danger mb-2">Remove Edge</button>
                </form>
            </div>
        </div>

        <div class="text-center">
            <form class="d-inline" action="/find_matching" method="post">
                <button type="submit" class="btn btn-success mb-2">Find Max Matching</button>
            </form>
            <form class="d-inline" action="/reset_colors" method="post">
                <button type="submit" class="btn btn-secondary mb-2">Reset Colors</button>
            </form>
            <form class="d-inline" action="/clear_graph" method="post">
                <button type="submit" class="btn btn-warning mb-2">Clear Graph</button>
            </form>
        </div>

        <div id="graph" class="graph-container">{{graph|safe}}</div>
    </div>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def home_action(error=None, find_matching=False):
    if not find_matching:
        reset_edges_colors()
    # Проверка графа на двудольность
    is_bipartite = check_bipartite()

    # Визуализация графа
    net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")
    for node in G.nodes:
        net.add_node(node, color=G.nodes[node].get('color', "#e0e0e0"))
    for edge in G.edges:
        net.add_edge(edge[0], edge[1], color=G.edges[edge].get('color', '#e0e0e0'))
    net.save_graph("graph.html")
    with open("graph.html", "r") as f:
        graph_html = f.read()

    return render_template_string(html_template, graph=graph_html, is_bipartite=is_bipartite, error=error)


def check_bipartite() -> Tuple[bool, dict]:
    color_map = {}
    for edge in G.edges():
        node1, node2 = edge
        node1_color = G.nodes[node1].get('color')
        node2_color = G.nodes[node2].get('color')
        color_map[node1] = node1_color
        color_map[node2] = node2_color
        # Если узлы имеют одинаковый цвет, граф не является двудольным
        if node1_color == node2_color:
            return False, color_map
    return True, color_map


@app.route("/add_node", methods=["POST"])
def add_node_action():
    node_name = request.form.get("node")
    color = request.form.get("color")
    if not G.has_node(node_name):
        G.add_node(node_name, color=color)
        return home_action()
    return home_action(error=f"Node '{node_name}' already exists")


@app.route("/add_edge", methods=["POST"])
def add_edge_action():
    node1 = request.form.get("node1")
    node2 = request.form.get("node2")
    if not G.has_node(node1) and not G.has_node(node2):
        return home_action(error=f"Node '{node1}' does not exist. Node '{node2}' does not exist.")
    if not G.has_node(node1):
        return home_action(error=f"Node '{node1}' does not exist")
    if not G.has_node(node2):
        return home_action(error=f"Node '{node2}' does not exist")

    if not G.has_edge(node1, node2):
        node1_color = G.nodes[node1].get('color')
        node2_color = G.nodes[node2].get('color')
        if node1_color == node2_color:
            return home_action(error="For a bipartite graph, it is impossible "
                                     "to connect vertices from the same fraction.")
        G.add_edge(node1, node2)
    return home_action()


@app.route("/remove_node", methods=["POST"])
def remove_node_action():
    node = request.form.get("node")
    if G.has_node(node):
        G.remove_node(node)
    return home_action()


@app.route("/remove_edge", methods=["POST"])
def remove_edge_action():
    node1 = request.form.get("node1")
    node2 = request.form.get("node2")
    if G.has_edge(node1, node2):
        G.remove_edge(node1, node2)
    return home_action()


def kunh_max_matching(G):
    # Получаем множества вершин для каждой доли, проверяем двудольность графа
    is_bipartite, color_map = check_bipartite()
    if not is_bipartite:
        raise ValueError("Graph is not bipartite, maximal matching cannot be found using Kuhn's algorithm")

    # Инициализация структур данных
    match = {v: None for v in G.nodes()}  # Используем идентификаторы вершин вместо индексов
    visited = set()

    def try_kuhn(v):
        # Проверяем только непомеченные вершины
        if v in visited:
            return False
        visited.add(v)
        for to in G[v]:  # Перебор смежных вершин
            if match[to] is None or try_kuhn(match[to]):
                match[to] = v
                return True
        return False

    # Перебор для вершин одной доли
    for v in color_map:
        if color_map[v] == 'blue':  # Предполагаем, что синяя доля - первая доля двудольного графа
            visited.clear()
            try_kuhn(v)

    # Восстановление паросочетания
    matching = []
    for v in G.nodes():
        if match[v] is not None:
            matching.append((v, match[v]))

    return matching


@app.route("/find_matching", methods=["POST"])
def find_matching_action():
    global G
    # Находим максимальное паросочетание с использованием networkx
    matching = kunh_max_matching(G)

    # Окрашиваем рёбра паросочетания в красный цвет
    for u, v in G.edges():
        if (u, v) in matching or (v, u) in matching:
            G.edges[u, v]['color'] = "red"
        else:
            G.edges[u, v]['color'] = "#e0e0e0"

    # Возвращаем обновлённый граф в шаблон
    return home_action(find_matching=True)


def reset_edges_colors():
    global G
    for u, v in G.edges:
        G.edges[u, v]['color'] = "#e0e0e0"


@app.route("/reset_colors", methods=["POST"])
def reset_edges_colors_action():
    reset_edges_colors()
    return home_action()


@app.route("/clear_graph", methods=["POST"])
def clear_graph_action():
    global G
    G.clear()
    return home_action()


if __name__ == "__main__":
    app.run(debug=True)
