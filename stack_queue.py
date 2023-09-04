class Node:
    def __init__(self, data) -> None:
        self.data = data
        self.next = None


class Stack:
    def __init__(self) -> None:
        self.head = None

    def push(self, val):
        node = Node(val)
        if not self.head:
            self.head = node
        else:
            node.next = self.head
            self.head = node

    def pop(self):
        node = self.head.next
        self.head = node

    def __str__(self):
        node = self.head
        s = f"{node.data}->"
        while node.next:
            node = node.next
            s += f"{node.data}->"
        return s


stack = Stack()
print("adding 1,2,3")
stack.push(1)
stack.push(2)
stack.push(3)
print(stack)
stack.pop()
print(stack)


class Queue:
    def __init__(self) -> None:
        self.head = None

    def enqueue(self, val):
        node = Node(val)
        if not self.head:
            self.head = node
        else:
            test_node = self.head
            while test_node.next:
                test_node = test_node.next
            test_node.next = node

    def dequeue(self):
        self.head = self.head.next

    def __str__(self):
        node = self.head
        s = f"{node.data}->"
        while node.next:
            node = node.next
            s += f"{node.data}->"
        return s


queue = Queue()
print("adding 1,2,3")
queue.enqueue(1)
queue.enqueue(2)
queue.enqueue(3)
print(queue)
queue.dequeue()
print(queue)
