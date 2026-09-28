# BFS & DFS Graph Search

A Python desktop application demonstrating and comparing two blind search algorithms: **Breadth-First Search (BFS)** and **Depth-First Search (DFS)**.

The application starts with a predefined graph, but the graph can be fully edited manually.

## Features

* Run **BFS or DFS** on the same graph.
* Add and remove vertices and edges.
* Move vertices with the mouse.
* Convert individual edges between directed and undirected.
* Select the start and target vertices.
* Visualize the search process step by step.
* Compare BFS and DFS results under the same conditions.
* Display the found path and search statistics.

## BFS vs DFS

* **BFS** explores the graph level by level using a queue and finds the shortest path in an unweighted graph.
* **DFS** explores one branch as deeply as possible using a stack or recursion and does not guarantee the shortest path.

## Technologies

* Python 3
* Tkinter
* `collections`
* `math`
* `time`

## Running

```bash
python3 dfs_search.py
```
