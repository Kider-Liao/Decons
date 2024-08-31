import random
from Node import Node

node_num = 2
node_list = []
for _ in range(node_num):
    node_list.append(Node(random.randint(0, 99) // 10 * 10, 0))
