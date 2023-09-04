class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class LinkedList:
    def __init__(self):
        self.head = None

    def append(self, data):
        new_node = Node(data)
        if self.head is None:
            self.head = new_node
        else:
            curr_node = self.head
            while curr_node.next:
                curr_node = curr_node.next
            curr_node.next = new_node

    def __str__(self):
        curr_node = self.head
        print_str = ""
        while curr_node:
            print_str += str(curr_node.data) + " "
            curr_node = curr_node.next
        return print_str

    def reverse(self):
        curr = self.head
        new_head = None
        while curr.next:
            next = curr.next
            new_head = curr
            curr.next = None
            curr = next
        self.head = new_head


linked = LinkedList()

linked.append(1)
linked.append(2)
linked.append(3)
linked.append(4)
linked.append(5)


print(linked)
