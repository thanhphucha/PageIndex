import json
import glob
import argparse
import os
from dotenv import load_dotenv
from pageindex.utils import ChatGPT_API, get_text_of_pages, extract_json

load_dotenv()


def find_node(tree, node_id):
    """Recursively find a node by its node_id."""
    if isinstance(tree, dict):
        if tree.get("node_id") == node_id:
            return tree
        for child in tree.get("nodes", []):
            r = find_node(child, node_id)
            if r:
                return r
    elif isinstance(tree, list):
        for item in tree:
            r = find_node(item, node_id)
            if r:
                return r
    return None


def search_all(precedents_dir, results_dir, question, model):
    # Load all indexed trees
    tree_files = glob.glob(f"{results_dir}/*_structure.json")
    if not tree_files:
        print(json.dumps({"error": "No indexed documents found in results/"}))
        return

    all_results = []

    for tree_path in tree_files:
        with open(tree_path) as f:
            tree_data = json.load(f)

        # Get the tree structure
        structure = tree_data.get("structure", tree_data)
        doc_name = tree_data.get("doc_name",
                     os.path.basename(tree_path).replace("_structure.json", ""))

        # Phase 1: LLM tree search — find relevant nodes
        tree_prompt = f"""You are a legal research assistant. Given a query and a contract's tree structure,
find all nodes that are likely to contain relevant clauses.

Query: {question}

Document: {doc_name}
Tree structure:
{json.dumps(structure, indent=2)}

Reply in JSON format only:
{{"node_list": ["0001", "0002"]}}

If no nodes are relevant, reply: {{"node_list": []}}"""

        result = ChatGPT_API(model, tree_prompt)
        parsed = extract_json(result)
        node_ids = parsed.get("node_list", [])

        if not node_ids:
            continue

        # Phase 2: Extract text from PDF
        pdf_name = doc_name + ".pdf"
        pdf_path = os.path.join(precedents_dir, pdf_name)

        if not os.path.exists(pdf_path):
            # Try finding the PDF by partial name match
            for f in os.listdir(precedents_dir):
                if f.lower().endswith(".pdf") and doc_name.lower() in f.lower():
                    pdf_path = os.path.join(precedents_dir, f)
                    break

        for nid in node_ids:
            node = find_node(structure, nid)
            if node and os.path.exists(pdf_path):
                text = get_text_of_pages(
                    pdf_path,
                    node["start_index"],
                    node["end_index"]
                )
                all_results.append({
                    "source": pdf_name,
                    "section": node.get("title", "Unknown"),
                    "pages": f"{node['start_index']}-{node['end_index']}",
                    "text": text.strip()
                })

    print(json.dumps(all_results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Search precedent contracts using PageIndex")
    p.add_argument("--precedents_dir", default="./precedents",
                   help="Directory containing precedent PDF files")
    p.add_argument("--results_dir", default="./results",
                   help="Directory containing indexed JSON tree files")
    p.add_argument("--question", required=True,
                   help="The clause or topic to search for")
    p.add_argument("--model", default="Qwen/Qwen3.5-35B-A3B",
                   help="LLM model name served by vLLM")
    args = p.parse_args()

    search_all(args.precedents_dir, args.results_dir, args.question, args.model)
