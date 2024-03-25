from fuzzywuzzy import fuzz
from unidecode import unidecode
import pycountry
import locale

countries = [c.name for c in pycountry.countries] + ['USA', 'UK']
countries_abbr = {c.name:c.alpha_2 for c in pycountry.countries}
countries_map = {'UK':'GB'}
countries_map.update({sd.code.split('-')[-1]:(sd.code.split('-')[0] + ', US') for sd in pycountry.subdivisions.get(country_code='US')})
countries_map.update({c.alpha_3:c.alpha_2 for c in pycountry.countries})
countries_map.update({c.alpha_2:c.alpha_2 for c in pycountry.countries})
countries_map.update({c.name.split(',')[0].upper():c.alpha_2 for c in pycountry.countries})
countries_map.update({c.official_name.split(',')[0].upper():c.alpha_2 for c in pycountry.countries})

def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)

def shorten_affil(s):
    s = s.replace("People's Republic of China", 'China')
    s = s.replace('United Kingdom', 'UK')
    s = s.replace('The Netherlands', 'NL')
    s = s.replace('the Netherlands', 'NL')
    s = s.replace('Germany, DE', 'DE')
    s = s.replace('U.S.A.', 'USA')
    s = s.replace('Inc.', 'USA')
    s = s.replace('United States', 'USA')
    s = s.replace('(United States)', ', USA')
    s = s.replace('United States of America', 'USA')
    s = s.replace(' g.bruzual@crya.unam.mx', '')
    s = s.replace('U.K.', 'UK')
    s = s.replace('UK.', 'UK')
    s = s.replace('Max Planck Institute', 'MPI')
    s = s.replace('Max Planck Institut', 'MPI')
    s = s.replace('Max Planck Inst.', 'MPI')
    s = s.replace('Max-Planck-Institute', 'MPI')
    s = s.replace('Max-Planck-Institut', 'MPI')
    s = s.replace('MPI for Astronomy', 'MPIA')
    s = s.replace('MPI fuer Astronomie', 'MPIA')
    s = s.replace('MPI für Astronomie', 'MPIA')
    s = s.replace('MPI fuer Astrophysik', 'MPIA')
    s = s.replace('MPIA-Heidelberg', 'MPIA')
    s = s.replace('Observatory of the Carnegie Institute', 'Carnegie Observatory')
    s = s.replace('Technical University', 'TU')
    s = s.replace('UC, Pontificia', 'PUC')
    s = s.replace('Pontifical Catholic University', 'PUC')
    s = s.replace('Pontificia Universidad Católica', 'PUC')
    s = s.replace('AEI Hannover (Hannover', 'Albert-Einstein-Institut, Hannover,')
    s = s.replace('MPI für Gravitationsphysik (Albert Einstein Institut)', 'Albert-Einstein-Institut, Hannover,')
    s = s.replace('MPI für Gravitationsphysik (Albert-Einstein-Institut)', 'Albert-Einstein-Institut, Hannover,')
    s = s.replace('MPI for Gravitational Physics (Albert Einstein Institute)', 'Albert-Einstein-Institut, Hannover,')
    s = s.replace('Albert-Einstein-Institut, MPI für Gravitationsphysik', 'Albert-Einstein-Institut, Hannover,')
    s = s.replace('California Institute of Technology', 'Caltech')
    s = s.replace('Center for Computational Astrophysics', 'CCA')

    s = s.replace('University of ', 'U ')
    s = s.replace('Center for Astrophysics', 'CfA')
    s = s.replace('University', 'U ')
    s = s.replace('Universite', 'U ')
    s = s.replace('Universitad de', 'U ')
    s = s.replace('Universitad', 'U ')
    s = s.replace('Universidad', 'U ')
    s = s.replace('Universität', 'U ')
    s = s.replace('U. ', 'U ')
    s = s.replace('Department for ', '')
    s = s.replace('Department of ', '')
    s = s.replace('Institute for ', '')
    #s = s.replace('Department', 'Dep')
    s = s.replace('Faculty', 'Fac')
    s = s.replace('Facultad', 'Fac')
    s = s.replace('Institute', 'Inst')
    s = s.replace('Instituto', 'Inst')
    s = s.replace('Observatory', 'Obs.')
    s = s.replace('Observatories', 'Obs.')
    s = s.replace('Departamento de', 'D')
    s = s.replace('Departamento', 'D')
    #s = s.replace(' of ', ' ')
    s = s.replace(' and ', '&')
    #s = s.replace(' for ', ' ')
    #s = s.replace(' fuer ', ' ')
    s = s.replace('&amp;', '&')
    s = s.replace('Sciences', 'Sci')
    s = s.replace('Science', 'Sci')
    s = s.replace('Mathematics', 'Math')
    s = s.replace('Medical', 'Med')
    s = s.replace('Physics', 'Phys')
    s = s.replace('Astronomy', 'Astro')
    s = s.replace('Harvard-Smitsonian', 'Harvard-Smithsonian')
    s = s.replace('Astrophysics', 'Astro')
    s = s.replace('Astrophysical Sci', 'Astro')
    s = s.replace('Astrophysik', 'Astro')
    s = s.replace('Biology', 'Bio')
    s = s.replace('&gt,Present address:', '')
    s = s.replace('&gt;Present address:', '')
    s = s.replace('Muenchen', 'München')
    s = s.replace('Munchen', 'München')
    s = s.replace('Garching bei München', 'Garching')
    s = s.replace('  ', ' ').replace(' , ', ', ').strip(" .)")
    parts = [p.strip() for p in s.split(',') if not has_numbers(p.strip())]
    if len(parts) == 0:
        return ''
    interesting_parts = []
    for p in parts:
        if p not in interesting_parts:
            interesting_parts.append(p)
    country = countries_map.get(interesting_parts[-1].upper(), interesting_parts[-1])
    return ', '.join(interesting_parts[:-1][:2]) + ', ' + country

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
    # custom rules
    if shorten_affil(a).startswith('Albert-Einstein-Institut') and shorten_affil(b).startswith('Albert-Einstein-Institut'):
        return True
    if shorten_affil(a) == 'Astro, ' + shorten_affil(b) or shorten_affil(b) == 'Astro, ' + shorten_affil(a):
        return True
    if bnorm2.endswith(anorm2) and a.startswith('Astro, '):
        return True
    if anorm2.endswith(bnorm2) and b.startswith('Astro, '):
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
