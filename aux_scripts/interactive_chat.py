import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from app.services.rag_service import generate_response

def main():
    print("--- RAG Agent CLI (Type 'quit' to exit) ---")
    print("Note: Ensure you have your API keys set in .env")
    chat_history = []
    
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ["quit", "exit"]:
                break
            
            if not user_input.strip():
                continue
                
            response = generate_response(user_input, chat_history)
            answer = response["answer"]
            print(f"Agent: {answer}")
            
            # Update history
            chat_history.append({"role": "user", "content": user_input})
            chat_history.append({"role": "assistant", "content": answer})
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
