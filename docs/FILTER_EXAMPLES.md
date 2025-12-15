# Nodi Filter Examples

Guide to using filters in Nodi REPL and CLI.

## Filter Syntax

Nodi supports jq-style filtering with two syntaxes:

```bash
# With 'jq' keyword
users | jq length

# Without 'jq' keyword (cleaner)
users | length
users | .name
users | .[0].id
```

Both work the same way!

## Built-in Filters (No pyjq Required)

These filters work out of the box without installing pyjq:

### 1. Identity
```bash
# Return data as-is
users | .
```

### 2. Length
```bash
# Get array or object length
users | length
# Output: 100

user:1 | .address | length
# Output: (number of fields in address)
```

### 3. Field Access
```bash
# Get a specific field
user:1 | .name
# Output: "Leanne Graham"

user:1 | .email
# Output: "Sincere@april.biz"
```

### 4. Nested Field Access
```bash
# Access nested fields with dot notation
user:1 | .address.city
# Output: "Gwenborough"

user:1 | .address.geo.lat
# Output: "-37.3159"
```

### 5. Array Index
```bash
# Get specific array element
users | .[0]
# Output: First user object

users | .[5]
# Output: User at index 5
```

### 6. Array Index with Field
```bash
# Get field from array element
users | .[0].name
# Output: "Leanne Graham"

users | .[3].email
# Output: Email of 4th user
```

### 7. Array Iteration
```bash
# Get all items (returns array)
users | .[]
# Output: All user objects
```

### 8. Keys
```bash
# Get object keys
user:1 | keys
# Output: ["id", "name", "username", "email", ...]
```

### 9. Values
```bash
# Get object values
user:1 | .address | values
# Output: All address field values
```

### 10. Type
```bash
# Get data type
users | type
# Output: "array"

user:1 | .name | type
# Output: "string"

user:1 | .id | type
# Output: "number"
```

## REPL Examples

### Example Session 1: User Exploration
```bash
$ python -m nodi

nodi> use jsonplaceholder.dev
Service: jsonplaceholder
Environment: dev

nodi [jsonplaceholder.dev]> users | length
Status: 200 (234ms)
100

nodi [jsonplaceholder.dev]> users | .[0]
Status: 200 (198ms)
{
  "id": 1,
  "name": "Leanne Graham",
  "username": "Bret",
  "email": "Sincere@april.biz",
  ...
}

nodi [jsonplaceholder.dev]> users | .[0].name
Status: 200 (201ms)
"Leanne Graham"

nodi [jsonplaceholder.dev]> user:1 | .address.city
Status: 200 (156ms)
"Gwenborough"
```

### Example Session 2: Using Different Filters
```bash
nodi [jsonplaceholder.dev]> user:1 | keys
Status: 200 (145ms)
["address", "company", "email", "id", "name", "phone", "username", "website"]

nodi [jsonplaceholder.dev]> user:1 | type
Status: 200 (132ms)
"object"

nodi [jsonplaceholder.dev]> users | type
Status: 200 (178ms)
"array"
```

### Example Session 3: Nested Data
```bash
nodi [jsonplaceholder.dev]> user:1 | .address
Status: 200 (145ms)
{
  "street": "Kulas Light",
  "suite": "Apt. 556",
  "city": "Gwenborough",
  "zipcode": "92998-3874",
  "geo": {
    "lat": "-37.3159",
    "lng": "81.1496"
  }
}

nodi [jsonplaceholder.dev]> user:1 | .address.geo.lat
Status: 200 (139ms)
"-37.3159"
```

## CLI Examples

### Using Filters in CLI Mode
```bash
# Get length
python -m nodi request jsonplaceholder.dev@users --filter "length"
# Output: 100

# Get specific field
python -m nodi request jsonplaceholder.dev@user:1 --filter ".name"
# Output: "Leanne Graham"

# Get nested field
python -m nodi request jsonplaceholder.dev@user:1 --filter ".address.city"
# Output: "Gwenborough"

# Get array element
python -m nodi request jsonplaceholder.dev@users --filter ".[0].name"
# Output: "Leanne Graham"

# Get keys
python -m nodi request jsonplaceholder.dev@user:1 --filter "keys"
# Output: ["address", "company", ...]

# Get type
python -m nodi request jsonplaceholder.dev@users --filter "type"
# Output: "array"
```

## Combining with Output Formats

### Filter + Table
```bash
nodi [jsonplaceholder.dev]> users | .[0]
# Then switch to table format
nodi [jsonplaceholder.dev]> format table
nodi [jsonplaceholder.dev]> users | .[0]
# Shows single user as table
```

### Filter + YAML
```bash
nodi [jsonplaceholder.dev]> format yaml
nodi [jsonplaceholder.dev]> user:1 | .address
# Shows address in YAML format
```

## Advanced Filters (Require pyjq)

These filters require installing pyjq (Unix/Linux/WSL only):

```bash
# Select/filter arrays
users | .[] | select(.id > 5)

# Map transformations
users | map({name, email})

# Complex expressions
users | .[] | select(.address.city == "Gwenborough") | .name

# Arithmetic
users | length / 10

# And more...
```

To install pyjq:
```bash
# Unix/Linux/macOS
pip install pyjq

# Windows - use WSL
wsl
pip install pyjq
```

## Filter Comparison

| Filter | Built-in | pyjq Required |
|--------|----------|---------------|
| `length` | ✅ | ✅ |
| `.field` | ✅ | ✅ |
| `.[n]` | ✅ | ✅ |
| `.[n].field` | ✅ | ✅ |
| `.a.b.c` | ✅ | ✅ |
| `.[]` | ✅ | ✅ |
| `keys` | ✅ | ✅ |
| `values` | ✅ | ✅ |
| `type` | ✅ | ✅ |
| `select()` | ❌ | ✅ |
| `map()` | ❌ | ✅ |
| Complex expressions | ❌ | ✅ |

## Tips

1. **No need for 'jq' keyword**: Both `users | jq length` and `users | length` work
2. **Case sensitive**: Field names are case sensitive
3. **Array indices**: Start from 0
4. **Error messages**: If a filter doesn't work, you'll see which mode you're in
5. **Combine filters**: You can chain operations (with pyjq)

## Troubleshooting

### Filter doesn't work
```bash
# Error: Filter 'xxx' not supported in simple mode
# Solution: Either simplify the filter or install pyjq
```

### No output
```bash
# Check if field exists
users | .[0] | keys
# Then access the correct field name
```

### Type error
```bash
# Check data type first
users | type
# Then use appropriate filter
```

## Quick Reference

```bash
# Common patterns
users | length                  # Count
users | .[0]                   # First item
users | .[0].name              # First item's field
user:1 | .address.city         # Nested field
user:1 | keys                  # List all fields
users | type                   # Check type
```

For more examples and advanced usage, see:
- [README.md](README.md)
- [QUICKSTART.md](QUICKSTART.md)
