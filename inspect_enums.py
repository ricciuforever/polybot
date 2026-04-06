import requests
import json
import config

def inspect_enum_values():
    subgraph = config.AZURO_SUBGRAPH
    print(f"--- INSPECTING ENUM VALUES ON {subgraph} ---")
    
    # Introspezione per trovare i valori validi del filtro status
    query = """
    {
      __type(name: "Game_filter") {
        inputFields {
          name
          type {
            name
            kind
            ofType {
              name
              kind
            }
          }
        }
      }
    }
    """
    try:
        resp = requests.post(subgraph, json={'query': query}, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            fields = data.get('data', {}).get('__type', {}).get('inputFields', [])
            status_field = [f for f in fields if f['name'] == 'status']
            if status_field:
                print(f"Status field type: {json.dumps(status_field[0], indent=2)}")
                # Se è un enum, cerchiamo i suoi valori
                type_name = status_field[0]['type']['name'] or status_field[0]['type']['ofType']['name']
                print(f"Looking for values of Enum: {type_name}")
                
                query_enum = """
                {
                  __type(name: "%s") {
                    enumValues {
                      name
                    }
                  }
                }
                """ % type_name
                resp_enum = requests.post(subgraph, json={'query': query_enum}, timeout=15)
                print(f"Enum values: {json.dumps(resp_enum.json(), indent=2)}")
            else:
                print("Status field NOT found in Game_filter.")
        else:
            print(f"Error {resp.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_enum_values()
