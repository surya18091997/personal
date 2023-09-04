from collections import defaultdict, deque
from typing import List


class Solution:
    def validPathBFS(
        self, n: int, edges: List[List[int]], source: int, destination: int
    ) -> bool:
        graph = defaultdict(list)
        for a, b in edges:
            graph[a].append(b)
            graph[b].append(a)
        visited = set()
        stack = []
        stack.append(source)
        while stack:
            current = stack.pop()
            print(current)
            visited.add(current)
            if current == destination:
                return True
            for next in graph[current]:
                if next not in visited:
                    stack.append(next)
        return False

    def validPathDFS(
        self, n: int, edges: List[List[int]], source: int, destination: int
    ) -> bool:
        ways = defaultdict(list)
        for i, j in edges:
            ways[i].append(j)
            ways[j].append(i)
        visited = set()
        stack = []
        stack.append(source)
        while stack:
            node = stack.pop()
            print(node)
            if node == destination:
                return True
            visited.add(node)
            for i in ways[node]:
                if i not in visited:
                    stack.append(i)
        return False


q = Solution()

print(q.validPathBFS(3, [[0, 1], [1, 2], [2, 0]], 0, 2))
print(q.validPathDFS(3, [[0, 1], [1, 2], [2, 0]], 0, 2))
