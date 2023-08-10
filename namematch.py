
def same_author(author, author2, verbose=False):
    """Check if a ADS author is the same as a github name"""
    # author: git log email name
    # author2: ADS publishing name
    name_parts = author2.lower().replace('.', '').strip().split(', ', maxsplit=1)
    if len(name_parts) == 1:
        lastnames, firstnames = name_parts[0], ''
    else:
        lastnames, firstnames = name_parts
    author2L = author.lower().replace('  ', ' ').replace('.', ' ').split('@')[0]
    initials = ''.join([p[0] for p in firstnames.split() + lastnames.replace('-', ' ').split() if len(p) > 0])
    if verbose: print('initials', initials)
    if author2L == initials:
        return True
    initials2 = ''.join([p[0] for p in lastnames.replace('-', ' ').split() + firstnames.split() if len(p) > 0])
    if verbose: print('initials2', initials)
    if author2L == initials2:
        return True
    if verbose: print('parts:', lastnames, '|', firstnames, '>', author2L)
    if author2L.startswith(lastnames + ' ' + firstnames):
        return True
    if author2L.startswith(firstnames):
        return True
    if (lastnames + ' ' + firstnames).startswith(author2L):
        return True
    for lastname in (lastnames.split('-') if '-' in lastnames else lastnames.split(' ')):
        if author2L == lastname:
            return True
        for firstname in firstnames, firstnames.lower().split(' ')[0], firstnames.lower().split(' ')[-1]:
            if len(firstname) > 4 and author2L == firstname:
                return True
            for sep in ' ', '', '_', '-':
                if verbose: print('  ', lastname + sep + firstname, author2L)
                # Johannes_Buchner == Buchner, Johannes
                if author2L == (lastname + sep + firstname):
                    return True
                # Buchner_Johannes == Buchner, Johannes
                if author2L == (firstname + sep + lastname):
                    return True
                # jbuchner == Buchner, Johannes
                if len(firstname) > 0 and author2L == (firstname[0] + lastname):
                    return True
                # johannes == Buchner, Johannes
                if author2L == (firstname).lower():
                    return True
            # Johannes Buchner == Buchner, J
            # Buchner Johannes == Buchner, J
            parts = author2L.split(' ')
            if len(parts) >= 2 and len(firstname) > 0:
                if verbose: print('  ', 'case B', parts, firstname[0], lastname)
                if len(parts[0]) > 0 and parts[0][0] == firstname[0] and parts[1] == lastname:
                    return True
                if len(parts[1]) > 0 and parts[1][0] == firstname[0] and parts[0] == lastname:
                    return True
            elif len(parts) == 1 and len(firstname) > 0:
                # johannesfrankbuchner == Buchner, J
                # buchnerjohannesfrank == Buchner, J
                if verbose: print('  ', 'case C', author2L, lastname, firstname)
                if author2L.startswith(lastname) and len(lastname) >= 4:
                    return True
                if author2L.endswith(lastname) and len(lastname) >= 4:
                    return True
                if author2L.startswith(firstname) and len(firstname) >= 5:
                    return True
                if author2L.endswith(firstname) and len(firstname) >= 5:
                    return True
    return False

if __name__ == '__main__':

    assert same_author("Johannes_Buchner", "Buchner, Johannes")
    assert same_author("JohannesBuchner", "Buchner, Johannes")
    assert same_author("BuchnerJohannes", "Buchner, Johannes")
    assert same_author("jbuchner", "Buchner, Johannes")
    assert same_author("jbuchner", "Buchner, J")
    assert same_author("Johannes_Buchner", "Buchner, J")
    assert same_author("JohannesBuchner", "Buchner, J")
    assert same_author("BuchnerJohannes", "Buchner, J")
    assert same_author("astertaylor", "Taylor, Aster G.")
    assert same_author("Dave Grote", "Grote, D. P.")
    assert same_author("Dave Grote", "Grote, D. P.")
    assert same_author("dfm", "Foreman-Mackey, Dan")
    assert same_author("dfm", "Foreman Mackey, Dan")
    
    count = 0
    count_same = 0
    for line in open('good_name_matches'):
        if line.startswith('### END'): break
        left, right = line.split(' || ')
        is_same = same_author(left[5:], right[:-2])
        print(is_same, left[5:], right[:-2])
        #assert is_same
        if is_same:
            count_same +=1
        count += 1
    print(count_same, count)
