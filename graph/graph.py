from groq import Groq
from graphviz import Digraph

# Initialize Groq client
client = Groq(api_key="api_key")

def generate_flowchart_text(topic):
    prompt = (
        f"You are a helpful educational assistant. Generate a simple flowchart for the topic: '{topic}'.\n"
        f"Respond ONLY in this format:\n"
        f"Start -> Step 1: ... -> Step 2: ... -> ... -> End"
    )

    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )

    return chat_completion.choices[0].message.content.strip()

def create_graphviz_flowchart(flow_text, filename="flowchart"):
    dot = Digraph()
    steps = [step.strip() for step in flow_text.split("->")]

    for i, step in enumerate(steps):
        dot.node(f"n{i}", step)
        if i > 0:
            dot.edge(f"n{i-1}", f"n{i}")

    dot.render(filename, format="png", cleanup=True)
    print(f"\n✅ Flowchart saved as '{filename}.png'")

def main():
    topic = input("Enter an educational topic: ")
    print("\n🧠 Generating flowchart using Groq...\n")

    flow_text = generate_flowchart_text(topic)
    print("📋 Flowchart Steps:\n", flow_text)

    create_graphviz_flowchart(flow_text)

if __name__ == "__main__":
    main()

