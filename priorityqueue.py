class PriorityQueue:
    def __init__(self):
        self.queue = []

    def enqueue(self, data, priority):
        self.queue.append((data, priority))
        self._heapify_up(len(self.queue) - 1)

    def dequeue(self):
        if not self.is_empty():
            data, _ = self.queue[0]
            last_element = self.queue.pop()
            if len(self.queue) > 0:
                self.queue[0] = last_element
                self._heapify_down(0)
            return data
        else:
            raise IndexError("Queue is empty")

    def is_empty(self):
        return len(self.queue) == 0

    def _heapify_up(self, index):
        while index > 0:
            parent_index = (index - 1) // 2
            if self.queue[index][1] < self.queue[parent_index][1]:
                # Swap with the parent if the priority is lower
                self.queue[index], self.queue[parent_index] = (
                    self.queue[parent_index],
                    self.queue[index],
                )
                index = parent_index
            else:
                break

    def _heapify_down(self, index):
        while True:
            left_child_index = 2 * index + 1
            right_child_index = 2 * index + 2
            smallest = index

            if (
                left_child_index < len(self.queue)
                and self.queue[left_child_index][1] < self.queue[smallest][1]
            ):
                smallest = left_child_index

            if (
                right_child_index < len(self.queue)
                and self.queue[right_child_index][1] < self.queue[smallest][1]
            ):
                smallest = right_child_index

            if smallest != index:
                # Swap with the smallest child if the priority is lower
                self.queue[index], self.queue[smallest] = (
                    self.queue[smallest],
                    self.queue[index],
                )
                index = smallest
            else:
                break


# Example usage:
pq = PriorityQueue()
pq.enqueue("Task 1", 3)
pq.enqueue("Task 2", 1)
pq.enqueue("Task 3", 2)

while not pq.is_empty():
    print(pq.dequeue())  # Outputs tasks in ascending order of priority
