#!/usr/bin/env python3
import sys
from bsky import get_feed, get_thread
from graph_tool.all import Graph

def build_threads_graph(client_handle: str, output_path: str, max_posts: int = 30) -> None:
    "Crea un graf dirigit on els nodes són usuaris que han participat en threads del client, i les arestes indiquen respostes."
    
    print(f"[i] Obtenint feed de '{client_handle}' ({max_posts} posts màxim)...")
    feed = get_feed(client_handle, limit=max_posts)
    print(f"[i] Recuperats {len(feed)} elements del feed.")

    g = Graph(directed=True)
    vprop_did = g.new_vertex_property("string")
    vprop_handle = g.new_vertex_property("string")
    eprop_weight = g.new_edge_property("int")
    g.vertex_properties["did"] = vprop_did
    g.vertex_properties["handle"] = vprop_handle
    g.edge_properties["weight"] = eprop_weight

    # Map DID → vertex
    did2v = {}

    def get_or_create_vertex(did: str, handle: str):
        if did in did2v:
            return did2v[did]
        v = g.add_vertex()
        vprop_did[v] = did
        vprop_handle[v] = handle
        did2v[did] = v
        return v

    def traverse_thread(thread, parent_did=None):
        curr_post = thread.post
        curr_did = curr_post.author.did
        curr_handle = curr_post.author.handle
        v_curr = get_or_create_vertex(curr_did, curr_handle)

        if parent_did:
            v_parent = get_or_create_vertex(parent_did[0], parent_did[1])
            e = g.edge(v_curr, v_parent)
            if e is None:
                e = g.add_edge(v_curr, v_parent)
                eprop_weight[e] = 1
            else:
                eprop_weight[e] += 1

        for reply in thread.replies:
            traverse_thread(reply, parent_did=(curr_did, curr_handle))

    print(f"[i] Recorreguent threads...")
    for idx, item in enumerate(feed, 1):
        if hasattr(item, "uri"):
            thread = get_thread(item.uri)
            traverse_thread(thread)
        if idx % 10 == 0 or idx == len(feed):
            print(f"    • Processats {idx}/{len(feed)} posts")

    print(f"[i] Guardant graf a '{output_path}'…")
    g.save(output_path)
    print("[✓] Fet!")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Ús: {sys.argv[0]} <client_handle> <fitxer_de_sortida.gt>")
        sys.exit(1)
    client_handle = sys.argv[1]
    output_path   = sys.argv[2]
    build_threads_graph(client_handle, output_path)
