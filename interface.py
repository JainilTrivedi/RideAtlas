from neo4j import GraphDatabase
from typing import List, Tuple

class Interface:
    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password), encrypted=False)
        self._driver.verify_connectivity()

    def close(self):
        self._driver.close()


    def bfs(self, start_node, last_node):
            # TODO: Implement this method
            #     raise NotImplementedError
            with self._driver.session() as session:
                session.run("CALL gds.graph.drop('myGraph', false)")
                session.run("""
                    CALL gds.graph.project(
                        'myGraph',
                        'Location',
                        '*',
                        {
                            relationshipProperties: 'distance'
                        }
                    )
                """)
                
                # Running BFS
                result = session.run("""
                    MATCH (start:Location {name: $start_node})
                    MATCH (end:Location {name: $last_node})
                    CALL gds.shortestPath.dijkstra.stream('myGraph', {
                        sourceNode: id(start),
                        targetNode: id(end),
                        relationshipWeightProperty: 'distance'
                    })
                    YIELD path
                    RETURN [node IN nodes(path) | {name: node.name}] AS path
                """, start_node=start_node, last_node=last_node)
                
                
                session.run("CALL gds.graph.drop('myGraph', false)")
                
                return list(result)

    def pagerank(self, max_iterations, weight_property):
        # TODO: Implement this method
        #     raise NotImplementedError

        with self._driver.session() as session:
            session.run("CALL gds.graph.drop('MyGraph',false)")
            if weight_property:
                property_exists = session.run("""
                    MATCH ()-[r]->()
                    WHERE r[$weight_property] IS NOT NULL
                    RETURN count(*) > 0 AS exists
                """, weight_property=weight_property).single()['exists']
            else:
                property_exists = False

            if property_exists:
                session.run("""
                    CALL gds.graph.project(
                        'myGraph',
                        'Location',
                        '*',
                        {
                            relationshipProperties: $weight_property
                        }
                    )
                """, weight_property=weight_property)
            else:
                session.run("""
                    CALL gds.graph.project(
                        'myGraph',
                        'Location',
                        '*'
                    )
                """)

            if property_exists:
                result = session.run("""
                    CALL gds.pageRank.write(
                        'myGraph',
                        {
                            maxIterations: $max_iterations,
                            relationshipWeightProperty: $weight_property,
                            writeProperty: 'pagerank'
                        }
                    ) YIELD nodePropertiesWritten
                    RETURN nodePropertiesWritten
                """, max_iterations=max_iterations, weight_property=weight_property)
            else:
                result = session.run("""
                    CALL gds.pageRank.write(
                        'myGraph',
                        {
                            maxIterations: $max_iterations,
                            writeProperty: 'pagerank'
                        }
                    ) YIELD nodePropertiesWritten
                    RETURN nodePropertiesWritten
                """, max_iterations=max_iterations)

            result = session.run("""
                MATCH (n:Location)
                WITH n, n.pagerank AS pagerank
                ORDER BY pagerank DESC
                WITH collect({name: n.name, score: pagerank}) AS sorted_nodes
                RETURN sorted_nodes[0] AS max_node, sorted_nodes[-1] AS min_node
            """)

            max_min_nodes = result.single()
            
            session.run("CALL gds.graph.drop('myGraph')")
            print(min)

        return max_min_nodes