class Node:
    def __init__(self, data=None, left=None, right=None) -> None:
        self.data = data
        self.left = left
        self.right = right


class BinaryTree:
    def __init__(self) -> None:
        self.root = None

    def insert(self, val):
        node = Node(val)
        if not self.root:
            self.root = node
            return
        self.insert_recursive(self.root, node)

    def insert_recursive(self, parent, node):
        if node.data < parent.data:
            if not parent.left:
                parent.left = node
            else:
                self.insert_recursive(parent.left, node)
        elif node.data > parent.data:
            if not parent.right:
                parent.right = node
            else:
                self.insert_recursive(parent.right, node)

    def inorder_traversal(self):
        results = []

        def recursive(node):
            if not node:
                return
            recursive(node.left)
            results.append(node.data)
            recursive(node.right)

        recursive(self.root)
        print(results)

    def preorder_traversal(self):
        results = []

        def recursive(node):
            if not node:
                return
            results.append(node.data)
            recursive(node.left)
            recursive(node.right)

        recursive(self.root)
        print(results)

    def postorder_traversal(self):
        results = []

        def recursive(node):
            if not node:
                return
            recursive(node.left)
            recursive(node.right)
            results.append(node.data)

        recursive(self.root)
        print(results)

    def reverseorder_traversal(self):
        results = []

        def recursive(node):
            if not node:
                return
            recursive(node.right)
            results.append(node.data)
            recursive(node.left)

        recursive(self.root)
        print(results)

    def bfs_or_level_traversal(self):
        queue = [self.root]
        res = []
        while queue:
            queue_cp = queue.copy()
            for i in queue_cp:
                node = queue.pop(0)
                res.append(node.data)
                if node.left:
                    queue.append(node.left)
                if node.right:
                    queue.append(node.right)
        print(res)


tree = BinaryTree()
tree.insert(5)
tree.insert(3)
tree.insert(8)
tree.insert(2)
tree.insert(4)
tree.insert(7)
tree.insert(9)

tree.inorder_traversal()
print("******")
tree.preorder_traversal()
print("******")
tree.postorder_traversal()
print("******")
tree.reverseorder_traversal()
print("******")
tree.bfs_or_level_traversal()
