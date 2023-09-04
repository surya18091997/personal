def merge_sort(arr):
    print("arr in recursion ", arr)
    if len(arr) <= 1:
        return

    mid = len(arr) // 2

    left = arr[:mid]
    right = arr[mid:]

    merge_sort(left)
    merge_sort(right)

    merge_two_sorted_lists(left, right, arr)


def merge_two_sorted_lists(a, b, arr):
    print("left ", a)
    print("right ", b)
    print("arr before ", arr)
    len_a = len(a)
    len_b = len(b)

    i = j = k = 0

    while i < len_a and j < len_b:
        if a[i] <= b[j]:
            arr[k] = a[i]
            i += 1
        else:
            arr[k] = b[j]
            j += 1
        k += 1

    while i < len_a:
        arr[k] = a[i]
        i += 1
        k += 1

    while j < len_b:
        arr[k] = b[j]
        j += 1
        k += 1
    print("sorted ", arr)


if __name__ == "__main__":
    test_cases = [[10, 3, 15, 7, 8, 23, 98, 29]]

    for arr in test_cases:
        merge_sort(arr)
        print(arr)
