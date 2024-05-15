from flask import Flask, render_template_string, request
from pyvis.network import Network
import networkx as nx

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
        {% endif %}
        
        <div class="row justify-content-center">
            <div class="col-12 col-md-6 mb-3">
                <form class="form-inline justify-content-center" action="/add_node" method="post">
                    <input type="text" class="form-control mb-2 mr-sm-2" name="node" placeholder="Node Name">
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
def home():
    # Проверка графа на двудольность и окрашивание вершин
    is_bipartite, color_map = check_bipartite(G)

    # Визуализация графа
    net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")
    for node in G.nodes:
        net.add_node(node, color=color_map.get(node, "#e0e0e0"))  # Стандартный цвет для вершин
    for edge in G.edges:
        net.add_edge(edge[0], edge[1], color=G.edges[edge].get('color', '#e0e0e0'))  # Стандартный цвет для рёбер
    net.save_graph("graph.html")
    with open("graph.html", "r") as f:
        graph_html = f.read()

    return render_template_string(html_template, graph=graph_html, is_bipartite=is_bipartite)


def check_bipartite(graph):
    if graph.number_of_nodes() == 0:
        return True, {}
    try:
        if nx.is_bipartite(graph):
            color_map = {}
            for node in nx.bipartite.sets(graph)[0]:
                color_map[node] = "blue"
            for node in nx.bipartite.sets(graph)[1]:
                color_map[node] = "yellow"
            return True, color_map
        else:
            return False, {}
    except nx.AmbiguousSolution:
        return False, {}


@app.route("/add_node", methods=["POST"])
def add_node():
    node = request.form.get("node")
    G.add_node(node)
    return home()


@app.route("/add_edge", methods=["POST"])
def add_edge():
    node1 = request.form.get("node1")
    node2 = request.form.get("node2")
    G.add_edge(node1, node2)
    return home()


@app.route("/remove_node", methods=["POST"])
def remove_node():
    node = request.form.get("node")
    if G.has_node(node):
        G.remove_node(node)
    return home()


@app.route("/remove_edge", methods=["POST"])
def remove_edge():
    node1 = request.form.get("node1")
    node2 = request.form.get("node2")
    if G.has_edge(node1, node2):
        G.remove_edge(node1, node2)
    return home()


def simple_max_matching(graph):
    # Формат графа предполагается dict, где ключ - вершина, значение - список смежных вершин
    visited = set()  # Множество посещенных вершин
    matching = []  # Список рёбер в паросочетании

    for node in graph:
        if node not in visited:
            for neighbour in graph[node]:
                # Если соседняя вершина не посещена, добавляем ребро в паросочетание
                if neighbour not in visited:
                    matching.append((node, neighbour))
                    visited.add(node)
                    visited.add(neighbour)
                    break  # Выходим из цикла, чтобы не добавлять лишние рёбра для одной вершины

    return matching


@app.route("/find_matching", methods=["POST"])
def find_matching():
    # Находим максимальное паросочетание с использованием networkx
    matching = simple_max_matching(G)

    # Окрашиваем рёбра паросочетания в красный цвет
    for u, v in G.edges():
        if (u, v) in matching or (v, u) in matching:
            G.edges[u, v]['color'] = "red"
        else:
            G.edges[u, v]['color'] = "#e0e0e0"

    # Возвращаем обновлённый граф в шаблон
    return home()


@app.route("/reset_colors", methods=["POST"])
def reset_colors():
    for edge in G.edges:
        G.edges[edge]['color'] = "#e0e0e0"
    return home()


@app.route("/clear_graph", methods=["POST"])
def clear_graph():
    global G
    G = nx.Graph()  # Пересоздаем граф, тем самым удаляя все вершины и ребра
    return home()


if __name__ == "__main__":
    app.run(debug=True)
