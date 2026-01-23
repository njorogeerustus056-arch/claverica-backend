import sys 
print("Checking Python path...") 
for i, path in enumerate(sys.path): 
    print(f"{i}: {path}") 
