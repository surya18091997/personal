class Node:
    def __init__(self, value=None, next=None) -> None:
        self.value = value
        self.next = next


class Head:
    def __init__(self, node=None) -> None:
        self.next = node


def create_linked_list_out_of_list(arr):
    node = nod = Head()
    for i in arr:
        next = Node(i)
        node.next = next
        node = next
    return nod


def print_linked_list(head):
    s = ""
    while head.next:
        head = head.next
        s = s + str(head.value)
        if head.next:
            s += "-->"
    return s


def insert_a_element_in_middle_of_linked_list(head, value, index):
    counter = 0
    return_head = head
    while head.next:
        head = head.next
        if counter == index:
            temp = head.next
            head.next = Node(value, temp)
            break
        counter += 1
    return return_head


def delete_a_element_in_middle_of_linked_list(head, index):
    counter = 0
    return_head = head
    while head.next:
        head = head.next
        if counter == index:
            temp = head.next
            head.next = temp.next
            del temp
            break
        counter += 1
    return return_head


def insert_a_element_in_start_of_linked_list(head, value):
    temp = head.next
    head.next = Node(value, temp)
    return head


def insert_a_element_in_end_of_linked_list(head, value):
    return_head = head
    while head.next:
        head = head.next
    head.next = Node(value)
    return return_head


def reverse_a_linked_list(head):
    new_head = Head()
    while head.next:
        head = head.next
        new_head = insert_a_element_in_start_of_linked_list(new_head, head.value)
    return new_head


data = [1, 2, 3, 5, 6, 7]
head = create_linked_list_out_of_list(data)
print(print_linked_list(head))
head = insert_a_element_in_middle_of_linked_list(head, 4, 2)
print(print_linked_list(head))
head = insert_a_element_in_middle_of_linked_list(head, 4, 2)
print(print_linked_list(head))
head = delete_a_element_in_middle_of_linked_list(head, 2)
print(print_linked_list(head))
head = insert_a_element_in_start_of_linked_list(head, 0)
print(print_linked_list(head))
head = insert_a_element_in_end_of_linked_list(head, 8)
print(print_linked_list(head))
reversed_head = reverse_a_linked_list(head)
print(print_linked_list(reversed_head))
