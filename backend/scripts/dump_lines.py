with open('services/auth_service.py','r', encoding='utf-8') as f:
    for i,l in enumerate(f,1):
        if 90 <= i <= 110:
            print(i, repr(l))
