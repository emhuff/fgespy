import graph_util
import itertools


class MeekRules:
    def __init__(self, undirect_unforced_edges=True):
        # Unforced parents should be undirected before orienting
        self.undirect_unforced_edges = undirect_unforced_edges
        self.node_subset = {}
        self.visited = set()
        self.direct_stack = []
        self.oriented = set({})

    def orient_implied_subset(self, graph, node_subset):
        self.node_subset = node_subset
        self.visited.update(node_subset)
        self.orient_using_meek_rules_locally(None, graph)

    def orient_implied(self, graph):
        self.orient_implied_subset(graph, graph.nodes())

    def orient_using_meek_rules_locally(self, knowledge, graph):
        oriented = set()

        if (self.undirect_unforced_edges):
            for node in self.node_subset:
                #TODO: undirect_unforced_edges
                self.undirect_unforced_edges_func(node, graph)
                self.direct_stack.extend(
                    graph_util.adjacent_nodes(graph, node))


        # TODO: Combine loops
        for node in self.node_subset:
            self.run_meek_rules(node, graph, knowledge)
        
        last_node = self.direct_stack.pop()
        while last_node is not None:
            # print(last_node)
            if (self.undirect_unforced_edges):
                #TODO: undirect_unforced_edges
                self.undirect_unforced_edges_func(last_node, graph)

            self.run_meek_rules(last_node, graph, knowledge)
            # print("past run_meek_rules")
            if (len(self.direct_stack) > 0):
                last_node = self.direct_stack.pop()
            else:
                last_node = None

    def undirect_unforced_edges_func(self, node, graph):
        parents_to_undirect = set()
        node_parents = graph_util.get_parents(graph, node)

        for parent in node_parents:
            def inner_loop(parent):
                for inner_parent in node_parents:
                    if inner_parent is not parent:
                        if not graph_util.adjacent(graph, parent, inner_parent):
                            self.oriented.add((parent, inner_parent))
                            return
                parents_to_undirect.add(parent)
            inner_loop(parent)


        
        add_to_direct_stack = False

        for parent in parents_to_undirect:
            #TODO: Must orient
            if not (parent, node) in self.oriented:
                graph_util.remove_edge(graph, parent, node)
                graph_util.add_undir_edge(graph, parent, node)
                self.visited.add(node)
                self.visited.add(parent)
                add_to_direct_stack = True
        
        if (add_to_direct_stack):
            for adjacent in graph_util.adjacent_nodes(graph, node):
                self.direct_stack.append(adjacent)
            
            self.direct_stack.append(node)


    def run_meek_rules(self, node, graph, knowledge):
        self.run_meek_rule_one(node, graph, knowledge)
        self.run_meek_rule_two(node, graph, knowledge)
        self.run_meek_rule_three(node, graph, knowledge)
        self.run_meek_rule_four(node, graph, knowledge)

    def run_meek_rule_one(self, node, graph, knowledge):
        """
                Meek's rule R1: if a-->b, b---c, and a not adj to c, then a-->c
                """
        # print("Running meek rule one", node)
        adjacencies = graph_util.adjacent_nodes(graph, node)
        if len(adjacencies) < 2:
            return
        all_combinations = itertools.combinations(
            range(0, len(adjacencies)), 2)
        # TODO: What do a and c represent here?
        for (index_one, index_two) in all_combinations:
            node_a = adjacencies[index_one]
            node_c = adjacencies[index_two]

            # TODO: Parallelize these flipped versions?
            self.r1_helper(node_a, node, node_c, graph, knowledge)
            self.r1_helper(node_c, node, node_a, graph, knowledge)

    def r1_helper(self, node_a, node_b, node_c, graph, knowledge):
        if ((not graph_util.adjacent(graph, node_a, node_c)) and graph_util.has_dir_edge(graph, node_a, node_b) and graph_util.has_undir_edge(graph, node_b, node_c)):
            if (not graph_util.is_unshielded_non_collider(graph, node_a, node_b, node_c)):
                return

            if self.is_arrowpoint_allowed(graph, node_b, node_c, knowledge):
                self.direct(node_b, node_c, graph)

    def direct(self, node_1, node_2, graph):
        graph_util.remove_edge(graph, node_1, node_2)
        graph_util.remove_edge(graph, node_2, node_1)
        graph_util.add_dir_edge(graph, node_1, node_2)
        self.visited.update([node_1, node_2])
        # node_1 -> node_2 edge
        if (node_1, node_2) not in self.oriented:
            self.oriented.add((node_1, node_2))
            self.direct_stack.append(node_2)

    def run_meek_rule_two(self, node_b, graph, knowledge):
        # print("Running meek rule two", node_b)
        adjacencies = graph_util.adjacent_nodes(graph, node_b)
        if len(adjacencies) < 2:
            return
        all_combinations = itertools.combinations(
            range(0, len(adjacencies)), 2)
        # TODO: What do a and c represent here?
        for (index_one, index_two) in all_combinations:
            node_a = adjacencies[index_one]
            node_c = adjacencies[index_two]

            # TODO: Parallelize these flipped versions?
            self.r2_helper(node_a, node_b, node_c, graph, knowledge)
            self.r2_helper(node_b, node_a, node_c, graph, knowledge)
            self.r2_helper(node_a, node_c, node_b, graph, knowledge)
            self.r2_helper(node_c, node_a, node_a, graph, knowledge)

    def r2_helper(self, a, b, c, graph, knowledge):
        if graph_util.has_dir_edge(graph, a, b) and graph_util.has_dir_edge(graph, b, c) and graph_util.has_undir_edge(graph, a, c):
            if self.is_arrowpoint_allowed(graph, a, c, knowledge):
                self.direct(a, c, graph)

    def run_meek_rule_three(self, node, graph, knowledge):
        # print("Running meek rule three", node)
        adjacencies = graph_util.adjacent_nodes(graph, node)
        if len(adjacencies) < 3:
            return

        for a_node in adjacencies:
            if (graph_util.has_undir_edge(graph, node, a_node)):
                copy_adjacencies = [a for a in adjacencies if a != a_node]
                all_combinations = itertools.combinations(
                    range(0, len(copy_adjacencies)), 2)

                for (index_one, index_two) in all_combinations:
                    node_b = adjacencies[index_one]
                    node_c = adjacencies[index_two]

                    if graph_util.is_kite(graph, node, a_node, node_b, node_c) and self.is_arrowpoint_allowed(graph, a_node, node):
                        if not graph_util.is_unshielded_non_collider(graph, node_c, node_b, a_node):
                            continue
                        self.direct(a_node, node, graph)
                        # TODO: Log

    def run_meek_rule_four(self, node, graph, knowledge):
        # TODO#Knowledge: This only runs when there is knowledge, so unimplemented for now
        pass

    def is_arrowpoint_allowed(self, graph, node_b, node_c, knowledge):
        # TODO#Knowledge implementation
        return True

    def get_visited(self):
        """ This is what FGES actually uses """
        return self.visited
