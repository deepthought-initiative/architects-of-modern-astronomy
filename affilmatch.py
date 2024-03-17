from fuzzywuzzy import fuzz
from unidecode import unidecode
import pycountry
import locale

countries = [c.name for c in pycountry.countries] + ['USA', 'UK']
countries_abbr = {c.name:c.alpha_2 for c in pycountry.countries}

def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)

def shorten_affil(s):
    s = s.replace('Max Planck Institute', 'MPE')
    s = s.replace('Technical University', 'TU')
    s = s.replace('University', '')
    s = s.replace('Department', '')
    s = s.replace('Faculty', '')
    s = s.replace('Institute', '')
    s = s.replace(' of ', '')
    s = s.replace(' and ', '&')
    s = s.replace('Sciences', 'Sci')
    s = s.replace('Science', 'Sci')
    s = s.replace('Mathematics', 'Math')
    s = s.replace('Medical', 'Med')
    s = s.replace('Physics', 'Phys')
    s = s.replace('Astronomy', 'Astro')
    s = s.replace('Biology', 'Bio')
    s = s.replace('  ', ' ').replace(' , ', ', ')
    parts = s.split(', ')
    interesting_parts = []
    for p in parts:
        if p not in interesting_parts and not has_numbers(p):
            interesting_parts.append(p)
    return ', '.join(interesting_parts[:2]) + ', ' + countries_abbr.get(interesting_parts[-1], interesting_parts[-1])

def split_by_countries(s):
    for c in countries:
        if ', ' + c + ', ' in s:
            parts = s.split(', ' + c + ', ', 1)
            if len(parts[1]) > 15:
                return [parts[0] + ', ' + c, parts[1]]
    return [s]

def split_affil_string(s):
    affils = []
    for part in s.split('; '):
        affils += split_by_countries(part)
    return affils

def replace_umlaute(s):
    umlaute = {'ü':'ue', 'Ü':'Ue', 'ä':'ae', 'Ä':'ae', 'ö':'oe', 'Ö':'Oe', 'ß':'ss'}
    for k, v in umlaute.items():
        s = s.replace(k, v)
    return s #.translate(umlaute)

def compare_unicode(s1, s2, verbose=False):
    u1 = unidecode(s1)
    u2 = unidecode(s2)
    if verbose:
        print("   a:", u1, "|", s1)
        print("   b:", u2, "|", s2)
    return u1 == u2 or u2.startswith(u1[:-1]) or u1.startswith(u2[:-1])

def compare(s1, s2, verbose=False, fuzz_min_ratio=80, fuzz_min_length=10):
    if compare_unicode(replace_umlaute(s1), replace_umlaute(s2), verbose=verbose):
        return True
    if compare_unicode(s1, s2, verbose=verbose):
        return True
    if len(s1) > fuzz_min_length and len(s2) > fuzz_min_length:
        fuzz_ratio = fuzz.ratio(s1, s2)
        if verbose:
            print("  fuzzy ratio:", fuzz_ratio, "for", s1, s2)
        return fuzz_ratio > fuzz_min_ratio

def _compare_old(s1, s2, verbose=False):
    #remove = string.punctuation
    #mapping = {ord(c): None for c in remove}
    #if verbose:
    #    print(f'Mapping: \n{mapping}')
    #t1 = s1.translate(mapping)
    #t2 = s2.translate(mapping)
    #t1 = s1
    #t2 = s2
    #u1 = NFD(NFD(t1).casefold()).strip()
    #u2 = NFD(NFD(t2).casefold()).strip()
    u1 = unidecode(s1)
    u2 = unidecode(s2)
    if verbose:
        print("   a:", u1)
        print("   b:", u2)
    if replace_umlaute(u1) == replace_umlaute(u2):
        return True
    return u1 == u2
    return locale.strcoll(u1, u2)


def is_affil_same(a, b, verbose=True):
    anorm = a.lower().replace('-', ' ').split('(')[0].split(',')[0].strip()
    bnorm = b.lower().replace('-', ' ').split('(')[0].split(',')[0].strip()
    if verbose:
        print("comparing affil::", anorm, bnorm)
    if compare(anorm, bnorm, verbose=verbose):
        return True
    anorm2 = a.lower().replace('-', ' ').split('(')[0].replace(',', ' ').strip()
    bnorm2 = b.lower().replace('-', ' ').split('(')[0].replace(',', ' ').strip()
    if verbose:
        print("comparing full affil::", anorm2, bnorm2)
    if compare(anorm2, bnorm2, verbose=verbose):
        return True
    if ', ' in a and ', ' in b:
        return compare(shorten_affil(a), shorten_affil(b), verbose=verbose)
    return False


if __name__ == '__main__':
    assert replace_umlaute("ü") == 'ue', replace_umlaute("ü")
    assert replace_umlaute("Ö") == 'Oe', replace_umlaute("Ö")
    assert compare("u", "ü", verbose=True)
    print(compare("u", "ü"))
    assert compare("u", "ü", verbose=True)
    print(compare("ue", "ü"))
    assert compare("ue", "ü", verbose=True)
    assert is_affil_same('Max-Planck-Institut fur Extraterrestrische Physik, Gieβenbachstraβe, 85748, Garching, Germany', 'Max-Planck-Institut für extraterrestrische Physik (MPE), Gießenbachstraße 1, 85748, Garching bei München, Germany')
    assert is_affil_same('Max-Planck-Institut für extraterrestrische Physik (MPE), Gießenbachstraße 1, 85748, Garching bei München, Germany', 'Max Planck Institute for Extraterrestrial Physics, Giessenbachstrasse, D-85741 Garching, Germany')
    assert is_affil_same('Max-Planck-Institut fur Extraterrestrische Physik, Gieβenbachstraβe, 85748, Garching, Germany', 'Max Planck Institute for Extraterrestrial Physics, Giessenbachstrasse, D-85741 Garching, Germany')
    same_set = [
        'Max-Planck-Institut für Extraterrestrische Physik, Giessenbachstraße 1, 85748, Garching bei München, Germany',
        'Max-Planck-Institut für extraterrestrische Physik, Giessenbachstraße 1, D-85748 Garching, Germany',
        'Max-Planck-Institut für extraterrestrische Physik, Giessenbachstraße 1, 85748, Garching bei München, Germany',
        'Max-Planck-Institut für extraterrestrische Physik, Giessenbachstrasse 1, D-85748 Garching, Germany',
        'Max-Planck-Institut für extraterrestrische Physik, Giessenbachstrasse 1, D-85748 Garching, Germany',
        'Max-Planck-Institut für extraterrestrische Physik, Gießenbachstraße 1, 85748, Garching, Germany',
        'Max-Planck-Institut für extraterrestrische Physik, Gießenbachstraße 1, 85748, Garching, Germany',
        'Max-Planck-Institut für Extraterrestrische Physik, Giessenbachstrasse 1, 85748, Garching, Germany'
    ]
    for a in same_set:
        for b in same_set:
            assert is_affil_same(a, b), (a, b)

    assert not is_affil_same('Max-Planck-Institut fur Extraterrestrische Physik, Gieβenbachstraβe, 85748, Garching, Germany', 'Instituto de Astrofísica and Centro de Astroingeniería, Facultad de Física, Pontificia Universidad Católica de Chile, Casilla 306, Santiago 22, Chile')
    assert not is_affil_same('AUT University', 'Instituto de Astrofísica and Centro de Astroingeniería, Facultad de Física, Pontificia Universidad Católica de Chile, Casilla 306, Santiago 22, Chile')
    assert not is_affil_same('Pontificia Universidad Católica de Chile, Instituto de Astrofísica, Casilla 306, Santiago 22, Chile', 'Instituto de Astrofísica and Centro de Astroingeniería, Facultad de Física, Pontificia Universidad Católica de Chile, Casilla 306, Santiago 22, Chile')
    
    parts = set(split_affil_string('University of Cambridge, Cambridge, United Kingdom, Max Planck Institute for Intelligent Systems, Tübingen, Germany'))
    assert parts == set(['University of Cambridge, Cambridge, United Kingdom', 'Max Planck Institute for Intelligent Systems, Tübingen, Germany']), parts

    parts = set(split_affil_string('University of Cambridge, Cambridge, United Kingdom; Max Planck Institute for Intelligent Systems, Tübingen, Germany'))
    print(parts)
    assert parts == set(['University of Cambridge, Cambridge, United Kingdom', 'Max Planck Institute for Intelligent Systems, Tübingen, Germany']), parts
    parts = set(split_affil_string('University of Cambridge, Cambridge, United Kingdom'))
    print(parts)
    assert parts == set(['University of Cambridge, Cambridge, United Kingdom']), parts
