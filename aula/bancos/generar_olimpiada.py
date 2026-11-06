"""Genera el banco de preguntas de la olimpiada de matemáticas de 6.º a 11.º (aula/bancos/olimpiada_6_11.json).

Cada grado tiene 40 preguntas de selección múltiple (4 opciones, una correcta) repartidas en los tres
pensamientos de la olimpiada: Newton (numérico y algebraico), Euclides (geométrico y métrico) y Bernoulli
(aleatorio: datos y probabilidad). Siguen los Derechos Básicos de Aprendizaje de cada grado.
Las respuestas se CALCULAN (no se escriben a mano) y las opciones equivocadas son errores típicos.

    python3 aula/bancos/generar_olimpiada.py
"""
import json
import math
import os
import random
from fractions import Fraction as F

random.seed(20261106)
NIVEL = {6: 'exploradores', 7: 'exploradores', 8: 'investigadores', 9: 'investigadores', 10: 'expertos', 11: 'expertos'}
CUPO = {'newton': 18, 'euclides': 14, 'bernoulli': 8}       # 40 por grado


def num(x):
    """Número con coma decimal (estilo colombiano): 2.5 → 2,5; 3.0 → 3."""
    if isinstance(x, F):
        return fr(x)
    if isinstance(x, float):
        x = round(x, 2)
        if x == int(x):
            return str(int(x))
        return f'{x}'.replace('.', ',')
    return str(x)


def fr(q):
    q = F(q)
    return str(q.numerator) if q.denominator == 1 else f'{q.numerator}/{q.denominator}'


def pi(c):
    """Coeficiente de π: pi(1) → π · pi(4) → 4π · pi('4/3') → 4/3π."""
    return 'π' if str(c) == '1' else f'{c}π'


def mono(c, e=1, v='x'):
    """Monomio bien escrito: mono(1, 3) → x^3 · mono(-1, 1) → −x · mono(7, 1) → 7x · mono(5, 0) → 5."""
    if e == 0:
        return str(c)
    coef = '' if c == 1 else '−' if c == -1 else str(c)
    return f'{coef}{v}' + ('' if e == 1 else ('²' if e == 2 else f'^{e}'))


def poli(*coefs):
    """poli(1, -5, 6) → x² − 5x + 6 (coeficientes de mayor a menor grado; los ceros no se escriben)."""
    n, partes = len(coefs) - 1, []
    for k, c in enumerate(coefs):
        e = n - k
        if c == 0:
            continue
        t = mono(abs(c), e)
        if not partes:
            partes.append(('−' if c < 0 else '') + t)
        else:
            partes.append(('− ' if c < 0 else '+ ') + t)
    return ' '.join(partes) or '0'


def _variar(texto, k):
    """El mismo texto con su primer número cambiado (para una opción falsa creíble): «52°» → «53°»."""
    import re
    f = re.fullmatch(r'(-?)(\d+)/(\d+)', texto.strip())
    if f:           # fracción: se cambia el denominador (así no queda «2/2» ni una igual a la correcta)
        n, d = int(f.group(2)), int(f.group(3))
        nd = d + k if d + k > n else d + abs(k) + n
        return f'{f.group(1)}{n}/{nd}'
    m = re.search(r'\d+(?:,\d+)?', texto)
    if not m:
        return f'{texto} ({k})'
    v = m.group(0)
    if ',' in v:
        nuevo = num(round(float(v.replace(',', '.')) + k * 0.5, 2))
    else:
        nuevo = str(max(0, int(v) + (k if int(v) + k >= 0 else abs(k) + 1)))
    return texto[:m.start()] + nuevo + texto[m.end():]


def distintos(correcta, candidatos, n=3):
    """n distractores distintos entre sí y de la correcta (como texto)."""
    vistos, out = {str(correcta)}, []
    for c in candidatos:
        s = str(c)
        if s not in vistos:
            vistos.add(s); out.append(s)
        if len(out) == n:
            return out
    for k in (1, -1, 2, -2, 3, 4, -3, 5, 10, 6):          # relleno, por si los errores típicos coinciden
        if len(out) == n:
            break
        s = _variar(str(correcta), k)
        if s not in vistos:
            vistos.add(s); out.append(s)
    return out


R = random.randint


# ---------------------------------------------------------------------------- 6.º
def g6():
    t = []
    # Newton
    def mcm():
        a, b = random.choice([(4, 6), (6, 8), (8, 12), (9, 12), (10, 15), (12, 18), (6, 10), (14, 21), (15, 20)])
        m = a * b // math.gcd(a, b)
        return ('newton', 'MCM', f'¿Cuál es el mínimo común múltiplo de {a} y {b}?', m, distintos(m, [a * b, math.gcd(a, b), m * 2]))
    def mcd():
        a, b = random.choice([(12, 18), (24, 36), (20, 30), (16, 40), (27, 45), (42, 56), (30, 45), (48, 60)])
        d = math.gcd(a, b)
        return ('newton', 'MCD', f'¿Cuál es el máximo común divisor de {a} y {b}?', d, distintos(d, [d // 2 or 1, d * 2, a * b // d]))
    def frac_suma():
        a, b = R(1, 4), R(2, 6)
        c, d = R(1, 4), R(2, 6)
        if a >= b or c >= d or b == d:
            return None
        r = F(a, b) + F(c, d)
        return ('newton', 'Fracciones', f'¿Cuánto es {a}/{b} + {c}/{d}?', fr(r), distintos(fr(r), [f'{a + c}/{b + d}', fr(F(a * c, b * d)), fr(r + F(1, b * d))]))
    def simplificar():
        n, d, k = R(1, 6), R(2, 9), R(2, 6)
        if n >= d or math.gcd(n, d) != 1:
            return None
        return ('newton', 'Fracciones', f'¿Cuál es la fracción {n * k}/{d * k} simplificada al máximo?', f'{n}/{d}',
                distintos(f'{n}/{d}', [f'{n * k // 2 if k % 2 == 0 else n * k}/{d * k // 2 if k % 2 == 0 else d}', f'{d}/{n}', f'{n}/{d + 1}']))
    def jerarquia():
        a, b, c, d = R(2, 9), R(2, 9), R(2, 6), R(1, 9)
        r = a + b * c - d
        return ('newton', 'Operaciones', f'¿Cuánto es {a} + {b} × {c} − {d}?', r, distintos(r, [(a + b) * c - d, a + b * (c - d), r + 2]))
    def potencia():
        b, e = R(2, 5), R(2, 4)
        return ('newton', 'Potencias', f'¿Cuánto es {b}^{e}?', b ** e, distintos(b ** e, [b * e, b ** (e - 1), b ** e + b]))
    def decimal():
        a, b = R(11, 99) / 10, R(11, 99) / 100
        r = round(a + b, 2)
        return ('newton', 'Decimales', f'¿Cuánto es {num(a)} + {num(b)}?', num(r), distintos(num(r), [num(round(a + b * 10, 2)), num(round(a * 10 + b, 2) / 10), num(round(r + 0.1, 2))]))
    def divisible():
        n = random.choice([126, 135, 248, 315, 462, 510, 225, 342])
        divs = [d for d in (2, 3, 4, 5, 9) if n % d == 0]
        no = [d for d in (2, 3, 4, 5, 9, 10) if n % d]
        if not divs or len(no) < 3:
            return None
        d = random.choice(divs)
        return ('newton', 'Divisibilidad', f'¿Entre cuál de estos números es divisible {n}?', d, distintos(d, random.sample(no, 3)))
    def primo():
        p = random.choice([29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73])
        return ('newton', 'Números primos', '¿Cuál de estos números es primo?', p, distintos(p, random.sample([39, 49, 51, 57, 63, 69, 77, 81, 87, 91], 3)))
    def problema():
        n, p = R(3, 9), R(1200, 4800) // 100 * 100
        return ('newton', 'Problemas', f'Un cuaderno cuesta ${p:,}'.replace(',', '.') + f'. ¿Cuánto pagan por {n} cuadernos?', f'${n * p:,}'.replace(',', '.'),
                distintos(f'${n * p:,}'.replace(',', '.'), [f'${(n - 1) * p:,}'.replace(',', '.'), f'${n * p + p:,}'.replace(',', '.'), f'${n + p:,}'.replace(',', '.')]))
    # Euclides
    def perimetro():
        a, b = R(3, 15), R(2, 12)
        return ('euclides', 'Perímetro', f'Un rectángulo mide {a} cm de largo y {b} cm de ancho. ¿Cuál es su perímetro?', f'{2 * (a + b)} cm',
                distintos(f'{2 * (a + b)} cm', [f'{a + b} cm', f'{a * b} cm', f'{2 * a + b} cm']))
    def area_rect():
        a, b = R(3, 15), R(2, 12)
        return ('euclides', 'Área', f'¿Cuál es el área de un rectángulo de {a} m por {b} m?', f'{a * b} m²', distintos(f'{a * b} m²', [f'{2 * (a + b)} m²', f'{a + b} m²', f'{a * b * 2} m²']))
    def angulo_comp():
        a = R(10, 80)
        return ('euclides', 'Ángulos', f'¿Cuánto mide el complemento de un ángulo de {a}°?', f'{90 - a}°', distintos(f'{90 - a}°', [f'{180 - a}°', f'{a}°', f'{360 - a}°']))
    def angulo_sup():
        a = R(20, 160)
        return ('euclides', 'Ángulos', f'¿Cuánto mide el suplemento de un ángulo de {a}°?', f'{180 - a}°', distintos(f'{180 - a}°', [f'{90 - a}°' if a < 90 else f'{a - 90}°', f'{360 - a}°', f'{a}°']))
    def triangulo():
        a, b = R(30, 80), R(30, 70)
        return ('euclides', 'Triángulos', f'Dos ángulos de un triángulo miden {a}° y {b}°. ¿Cuánto mide el tercero?', f'{180 - a - b}°',
                distintos(f'{180 - a - b}°', [f'{360 - a - b}°', f'{a + b}°', f'{90 - (a + b) % 90}°']))
    def cubo():
        l = R(2, 6)
        return ('euclides', 'Volumen', f'¿Cuál es el volumen de un cubo de {l} cm de arista?', f'{l ** 3} cm³', distintos(f'{l ** 3} cm³', [f'{l * l} cm³', f'{6 * l * l} cm³', f'{3 * l} cm³']))
    # Bernoulli
    def media():
        xs = [R(2, 10) for _ in range(4)]
        s = sum(xs) + (-sum(xs)) % 5
        xs.append(s - sum(xs) if s - sum(xs) > 0 else 5)
        m = F(sum(xs), 5)
        if m.denominator != 1:
            return None
        return ('bernoulli', 'Promedio', f'¿Cuál es el promedio de {", ".join(map(str, xs))}?', int(m), distintos(int(m), [sum(xs), int(m) + 1, sorted(xs)[2] if sorted(xs)[2] != int(m) else int(m) - 1]))
    def moda():
        base = random.sample(range(1, 10), 4)
        m = base[0]
        xs = base + [m, m]
        random.shuffle(xs)
        return ('bernoulli', 'Moda', f'¿Cuál es la moda de los datos {", ".join(map(str, xs))}?', m, distintos(m, base[1:]))
    def dado():
        caso = random.choice([('un número par', 3), ('un número mayor que 4', 2), ('el número 6', 1), ('un número menor que 3', 2), ('un múltiplo de 3', 2)])
        r = F(caso[1], 6)
        return ('bernoulli', 'Probabilidad', f'Se lanza un dado. ¿Cuál es la probabilidad de sacar {caso[0]}?', fr(r), distintos(fr(r), [f'{caso[1]}/{caso[1] + 6}', f'1/{caso[1] + 1}', fr(F(6 - caso[1], 6))]))
    t += [mcm, mcd, frac_suma, simplificar, jerarquia, potencia, decimal, divisible, primo, problema,
          perimetro, area_rect, angulo_comp, angulo_sup, triangulo, cubo, media, moda, dado]
    return t


# ---------------------------------------------------------------------------- 7.º
def g7():
    def enteros_suma():
        a, b = R(-20, -1), R(-15, 15)
        return ('newton', 'Números enteros', f'¿Cuánto es ({a}) + ({b})?', a + b, distintos(a + b, [a - b, -(a + b), abs(a) + abs(b)]))
    def enteros_mult():
        a, b = R(-9, -2), R(-9, 9)
        if b == 0:
            return None
        return ('newton', 'Números enteros', f'¿Cuánto es ({a}) × ({b})?', a * b, distintos(a * b, [-(a * b), a + b, a * b + 1]))
    def frac_mult():
        a, b, c, d = R(1, 5), R(2, 7), R(1, 5), R(2, 7)
        if a >= b or c >= d:
            return None
        r = F(a, b) * F(c, d)
        return ('newton', 'Fracciones', f'¿Cuánto es {a}/{b} × {c}/{d}?', fr(r), distintos(fr(r), [f'{a + c}/{b + d}', fr(F(a, b) / F(c, d)), fr(F(a * d, b * c * 2) if c else r + 1)]))
    def frac_div():
        a, b, c, d = R(1, 5), R(2, 7), R(1, 5), R(2, 7)
        if a >= b or c >= d or F(a, b) == F(c, d):
            return None
        r = F(a, b) / F(c, d)
        return ('newton', 'Fracciones', f'¿Cuánto es {a}/{b} ÷ {c}/{d}?', fr(r), distintos(fr(r), [fr(F(a, b) * F(c, d)), f'{a * c}/{b * d}', fr(F(c, d) / F(a, b))]))
    def porcentaje():
        p, v = random.choice([10, 15, 20, 25, 30, 40, 50, 75]), R(4, 40) * 20
        r = p * v // 100
        return ('newton', 'Porcentajes', f'¿Cuál es el {p} % de {v}?', r, distintos(r, [v - r, r * 2, p + v // 10]))
    def regla3():
        a, b, k = R(2, 6), R(3, 12) * 500, R(2, 5)
        return ('newton', 'Proporcionalidad', f'Si {a} kilos de arroz cuestan ${b:,}'.replace(',', '.') + f', ¿cuánto cuestan {a * k} kilos?', f'${b * k:,}'.replace(',', '.'),
                distintos(f'${b * k:,}'.replace(',', '.'), [f'${b * a * k:,}'.replace(',', '.'), f'${b + k:,}'.replace(',', '.'), f'${b * (k + 1):,}'.replace(',', '.')]))
    def inversa():
        a, d = R(2, 6), R(4, 12)
        k = random.choice([x for x in (2, 3, 4) if (a * d) % (a * x) == 0] or [2])
        b = a * k
        r = F(a * d, b)
        if r.denominator != 1:
            return None
        return ('newton', 'Proporcionalidad inversa', f'{a} obreros hacen una obra en {d} días. ¿En cuántos días la hacen {b} obreros (al mismo ritmo)?', f'{r} días',
                distintos(f'{r} días', [f'{d * k} días', f'{d + k} días', f'{d - 1} días']))
    def ecuacion():
        x, a, b = R(-6, 12), R(2, 7), R(-10, 15)
        if b == 0 or x == 0:
            return None
        return ('newton', 'Ecuaciones', f'Resuelva: {poli(a, b)} = {a * x + b}', f'x = {x}', distintos(f'x = {x}', [f'x = {-x}', f'x = {x + 1}', f'x = {a * x}']))
    def descuento():
        p, v = random.choice([10, 20, 25, 30]), R(2, 20) * 10000
        r = v - v * p // 100
        return ('newton', 'Porcentajes', f'Unos tenis cuestan ${v:,}'.replace(',', '.') + f' y tienen {p} % de descuento. ¿Cuánto se paga?', f'${r:,}'.replace(',', '.'),
                distintos(f'${r:,}'.replace(',', '.'), [f'${v * p // 100:,}'.replace(',', '.'), f'${v - p:,}'.replace(',', '.'), f'${v + v * p // 100:,}'.replace(',', '.')]))
    # Euclides
    def area_tri():
        b, h = R(3, 14) * 2, R(3, 12)
        return ('euclides', 'Área', f'¿Cuál es el área de un triángulo de base {b} cm y altura {h} cm?', f'{b * h // 2} cm²', distintos(f'{b * h // 2} cm²', [f'{b * h} cm²', f'{b + h} cm²', f'{2 * (b + h)} cm²']))
    def circulo():
        r = R(2, 10)
        return ('euclides', 'Círculo', f'¿Cuál es la longitud de una circunferencia de radio {r} cm? (use π ≈ 3,14)', f'{num(round(2 * 3.14 * r, 2))} cm',
                distintos(f'{num(round(2 * 3.14 * r, 2))} cm', [f'{num(round(3.14 * r * r, 2))} cm', f'{num(round(3.14 * r, 2))} cm', f'{num(round(2 * 3.14 * r + 1, 2))} cm']))
    def area_circ():
        r = R(2, 10)
        return ('euclides', 'Círculo', f'¿Cuál es el área de un círculo de radio {r} m? (use π ≈ 3,14)', f'{num(round(3.14 * r * r, 2))} m²',
                distintos(f'{num(round(3.14 * r * r, 2))} m²', [f'{num(round(2 * 3.14 * r, 2))} m²', f'{num(round(3.14 * 2 * r * 2 * r, 2))} m²', f'{r * r} m²']))
    def poligono():
        n = random.choice([5, 6, 8, 10, 12])
        s = (n - 2) * 180
        nombres = {5: 'pentágono', 6: 'hexágono', 8: 'octágono', 10: 'decágono', 12: 'dodecágono'}
        return ('euclides', 'Polígonos', f'¿Cuánto suman los ángulos internos de un {nombres[n]}?', f'{s}°', distintos(f'{s}°', [f'{n * 180}°', f'{360}°' if s != 360 else '540°', f'{(n - 1) * 180}°']))
    def escala():
        e, cm = random.choice([100, 200, 500, 1000]), R(2, 15)
        r = cm * e / 100
        return ('euclides', 'Escalas', f'En un plano a escala 1:{e}, una pared mide {cm} cm. ¿Cuánto mide en la realidad?', f'{num(float(r))} m',
                distintos(f'{num(float(r))} m', [f'{cm * e} m', f'{num(float(r) / 10)} m', f'{num(float(r) * 10)} m']))
    def prisma():
        a, b, c = R(2, 8), R(2, 6), R(2, 9)
        return ('euclides', 'Volumen', f'¿Cuál es el volumen de una caja de {a} cm × {b} cm × {c} cm?', f'{a * b * c} cm³', distintos(f'{a * b * c} cm³', [f'{a + b + c} cm³', f'{2 * (a * b + b * c + a * c)} cm³', f'{a * b} cm³']))
    # Bernoulli
    def media():
        xs = [R(3, 10) for _ in range(5)]
        s = sum(xs)
        if s % 5:
            xs[-1] += 5 - s % 5
        m = sum(xs) // 5
        return ('bernoulli', 'Promedio', f'Las notas de Ana son {", ".join(map(str, xs))}. ¿Cuál es su promedio?', m, distintos(m, [sum(xs), m + 1, max(xs)]))
    def mediana():
        xs = random.sample(range(1, 30), 5)
        m = sorted(xs)[2]
        return ('bernoulli', 'Mediana', f'¿Cuál es la mediana de {", ".join(map(str, xs))}?', m, distintos(m, [xs[2], sum(xs) // 5, sorted(xs)[1]]))
    def bolsa():
        r, a, v = R(2, 6), R(1, 5), R(1, 4)
        t = r + a + v
        p = F(r, t)
        pl = lambda n, s, p: f'{n} {s if n == 1 else p}'
        return ('bernoulli', 'Probabilidad', f'En una bolsa hay {pl(r, "balota roja", "balotas rojas")}, {pl(a, "azul", "azules")} y {pl(v, "verde", "verdes")}. Si se saca una sin mirar, ¿cuál es la probabilidad de que sea roja?', fr(p),
                distintos(fr(p), [f'{r}/{a + v}', f'1/{t}', fr(F(a + v, t))]))
    return [enteros_suma, enteros_mult, frac_mult, frac_div, porcentaje, regla3, inversa, ecuacion, descuento,
            area_tri, circulo, area_circ, poligono, escala, prisma, media, mediana, bolsa]


# ---------------------------------------------------------------------------- 8.º
def g8():
    def potencias():
        a, m, n = R(2, 5), R(2, 6), R(2, 5)
        return ('newton', 'Potencias', f'Simplifique: {a}^{m} · {a}^{n}', f'{a}^{m + n}', distintos(f'{a}^{m + n}', [f'{a}^{m * n}', f'{a * a}^{m + n}', f'{a}^{abs(m - n)}']))
    def potencia_cociente():
        a, m, n = R(2, 7), R(5, 9), R(2, 4)
        return ('newton', 'Potencias', f'Simplifique: {a}^{m} ÷ {a}^{n}', f'{a}^{m - n}', distintos(f'{a}^{m - n}', [f'{a}^{m + n}', f'{a}^{m // n}', f'1^{m - n}']))
    def raiz():
        n = R(4, 20)
        return ('newton', 'Radicación', f'¿Cuánto es √{n * n}?', n, distintos(n, [n * n // 2, n + 1, 2 * n]))
    def cientifica():
        m, e = random.choice([1.2, 3.5, 4.7, 6.02, 2.8, 9.1]), R(3, 7)
        valor = int(round(m * 10 ** e))
        txt = f'{valor:,}'.replace(',', '.')
        return ('newton', 'Notación científica', f'¿Cómo se escribe {txt} en notación científica?', f'{num(m)} × 10^{e}',
                distintos(f'{num(m)} × 10^{e}', [f'{num(m)} × 10^{e + 1}', f'{num(m * 10)} × 10^{e}', f'{num(m)} × 10^{e - 1}']))
    def cuadrado_binomio():
        a = R(2, 9)
        return ('newton', 'Productos notables', f'¿Cuál es el desarrollo de (x + {a})²?', f'x² + {2 * a}x + {a * a}', distintos(f'x² + {2 * a}x + {a * a}', [f'x² + {a * a}', f'x² + {a}x + {a * a}', f'x² + {2 * a}x + {2 * a}']))
    def diferencia_cuadrados():
        a = R(2, 12)
        return ('newton', 'Factorización', f'Factorice: x² − {a * a}', f'(x + {a})(x − {a})', distintos(f'(x + {a})(x − {a})', [f'(x − {a})²', f'(x + {a})²', f'(x − {a * a})(x + 1)']))
    def trinomio():
        p, q = R(1, 7), R(1, 7)
        s, m = p + q, p * q
        return ('newton', 'Factorización', f'Factorice: x² + {s}x + {m}', f'(x + {p})(x + {q})', distintos(f'(x + {p})(x + {q})', [f'(x + {s})(x + {m})', f'(x − {p})(x − {q})', f'(x + {m})(x + 1)' if m != s else f'(x + {p + 1})(x + {q})']))
    def factor_comun():
        a, b = R(2, 9), R(2, 9)
        return ('newton', 'Factorización', f'Factorice: {a * b}x² + {a}x', f'{a}x({b}x + 1)', distintos(f'{a}x({b}x + 1)', [f'{a}({b}x² + x)', f'x({a * b}x + 1)', f'{a}x({b}x − 1)']))
    def irracional():
        return ('newton', 'Números reales', '¿Cuál de estos números es irracional?', '√2', ['3/4', '0,25', '√16'])
    # Euclides
    def pitagoras():
        a, b, c = random.choice([(3, 4, 5), (6, 8, 10), (5, 12, 13), (8, 15, 17), (9, 12, 15), (7, 24, 25), (12, 16, 20)])
        return ('euclides', 'Teorema de Pitágoras', f'Los catetos de un triángulo rectángulo miden {a} y {b}. ¿Cuánto mide la hipotenusa?', c, distintos(c, [a + b, abs(b - a) + 1, c + 1]))
    def pitagoras_cateto():
        a, b, c = random.choice([(3, 4, 5), (6, 8, 10), (5, 12, 13), (8, 15, 17), (9, 12, 15)])
        return ('euclides', 'Teorema de Pitágoras', f'Una escalera de {c} m se apoya en una pared y su pie queda a {a} m de la pared. ¿A qué altura llega?', f'{b} m', distintos(f'{b} m', [f'{c - a} m', f'{c + a} m', f'{b + 1} m']))
    def area_trapecio():
        B, b, h = R(8, 16), R(3, 7), R(2, 9)
        if (B + b) * h % 2:
            return None
        return ('euclides', 'Área', f'Un trapecio tiene bases de {B} cm y {b} cm y altura {h} cm. ¿Cuál es su área?', f'{(B + b) * h // 2} cm²', distintos(f'{(B + b) * h // 2} cm²', [f'{(B + b) * h} cm²', f'{B * b * h} cm²', f'{B * h} cm²']))
    def volumen_cilindro():
        r, h = R(1, 5), R(2, 10)
        return ('euclides', 'Volumen', f'¿Cuál es el volumen de un cilindro de radio {r} cm y altura {h} cm? (deje π)', f'{pi(r * r * h)} cm³', distintos(f'{pi(r * r * h)} cm³', [f'{pi(2 * r * h)} cm³', f'{pi(r * h)} cm³', f'{pi(2 * r * r * h)} cm³']))
    def area_lateral():
        a, h = R(2, 8), R(3, 10)
        return ('euclides', 'Área', f'¿Cuál es el área lateral de un prisma de base cuadrada de lado {a} cm y altura {h} cm?', f'{4 * a * h} cm²', distintos(f'{4 * a * h} cm²', [f'{a * a * h} cm²', f'{4 * a * h + 2 * a * a} cm²', f'{2 * a * h} cm²']))
    # Bernoulli
    def dos_monedas():
        return ('bernoulli', 'Probabilidad', 'Se lanzan dos monedas. ¿Cuál es la probabilidad de que salgan dos caras?', '1/4', ['1/2', '1/3', '2/4'])
    def suma_dados():
        s = random.choice([2, 3, 4, 5, 6, 7, 8, 12])
        casos = sum(1 for a in range(1, 7) for b in range(1, 7) if a + b == s)
        p = F(casos, 36)
        return ('bernoulli', 'Probabilidad', f'Se lanzan dos dados. ¿Cuál es la probabilidad de que sumen {s}?', fr(p), distintos(fr(p), [f'1/{s}', f'{casos}/12', fr(F(1, 6)) if fr(p) != '1/6' else '1/12']))
    def rango():
        xs = random.sample(range(5, 60), 6)
        r = max(xs) - min(xs)
        return ('bernoulli', 'Estadística', f'¿Cuál es el rango de los datos {", ".join(map(str, xs))}?', r, distintos(r, [max(xs), sum(xs) // 6, max(xs) + min(xs)]))
    def frecuencia():
        n, k = random.choice([(20, 5), (40, 10), (25, 5), (50, 20), (30, 6)])
        return ('bernoulli', 'Estadística', f'En un curso de {n} estudiantes, {k} prefieren el fútbol. ¿Qué porcentaje es?', f'{k * 100 // n} %', distintos(f'{k * 100 // n} %', [f'{k} %', f'{n - k} %', f'{k * 100 // n + 5} %']))
    return [potencias, potencia_cociente, raiz, cientifica, cuadrado_binomio, diferencia_cuadrados, trinomio, factor_comun, irracional,
            pitagoras, pitagoras_cateto, area_trapecio, volumen_cilindro, area_lateral, dos_monedas, suma_dados, rango, frecuencia]


# ---------------------------------------------------------------------------- 9.º
def g9():
    def sistema():
        x, y = R(-4, 8), R(-4, 8)
        return ('newton', 'Sistemas de ecuaciones', f'Resuelva el sistema: x + y = {x + y}; x − y = {x - y}', f'x = {x}, y = {y}',
                distintos(f'x = {x}, y = {y}', [f'x = {y}, y = {x}', f'x = {x + y}, y = {x - y}', f'x = {-x}, y = {-y}']))
    def pendiente():
        x1, y1, x2 = R(-3, 4), R(-5, 5), R(5, 9)
        m = random.choice([-3, -2, -1, 1, 2, 3])
        y2 = y1 + m * (x2 - x1)
        return ('newton', 'Función lineal', f'¿Cuál es la pendiente de la recta que pasa por ({x1}, {y1}) y ({x2}, {y2})?', m, distintos(m, [-m, fr(F(x2 - x1, y2 - y1)), m * 2]))
    def lineal_valor():
        m, b, x = R(-4, 5), R(-6, 8), R(-3, 6)
        if m == 0:
            return None
        return ('newton', 'Función lineal', f'Si f(x) = {poli(m, b)}, ¿cuánto vale f({x})?', m * x + b, distintos(m * x + b, [m * x - b, m + x + b, m * (x + b)]))
    def cuadratica():
        r1, r2 = R(-6, 6), R(-6, 6)
        if r1 == r2 or r1 == -r2:
            return None
        s, p = -(r1 + r2), r1 * r2
        txt = poli(1, s, p)
        sol = f'x = {min(r1, r2)} y x = {max(r1, r2)}'
        return ('newton', 'Ecuación cuadrática', f'Resuelva: {txt} = 0', sol, distintos(sol, [f'x = {-max(r1, r2)} y x = {-min(r1, r2)}', f'x = {s} y x = {p}', f'x = {min(r1, r2)} y x = {max(r1, r2) + 1}']))
    def discriminante():
        a, b, c = R(1, 3), R(-6, 6), R(-5, 5)
        d = b * b - 4 * a * c
        r = 'Dos soluciones reales distintas' if d > 0 else 'Una solución real (doble)' if d == 0 else 'Ninguna solución real'
        otras = ['Dos soluciones reales distintas', 'Una solución real (doble)', 'Ninguna solución real', 'Infinitas soluciones']
        if c == 0:
            return None
        return ('newton', 'Ecuación cuadrática', f'¿Cuántas soluciones reales tiene {poli(a, b, c)} = 0?', r, [o for o in otras if o != r][:3])
    def interes():
        c, t, a = R(2, 20) * 100000, random.choice([2, 3, 5, 10]), R(1, 4)
        i = c * t * a // 100
        return ('newton', 'Interés simple', f'¿Cuánto interés simple producen ${c:,}'.replace(',', '.') + f' al {t} % anual durante {a} años?', f'${i:,}'.replace(',', '.'),
                distintos(f'${i:,}'.replace(',', '.'), [f'${c * t // 100:,}'.replace(',', '.'), f'${c + i:,}'.replace(',', '.'), f'${i * 2:,}'.replace(',', '.')]))
    # Euclides
    def thales():
        a, b, k = R(2, 6), R(3, 8), R(2, 4)
        return ('euclides', 'Teorema de Thales', f'Dos rectas paralelas cortan a dos transversales. En una se forman segmentos de {a} cm y {b} cm; en la otra, el que corresponde a {a} cm mide {a * k} cm. ¿Cuánto mide el otro?', f'{b * k} cm',
                distintos(f'{b * k} cm', [f'{b + k} cm', f'{a * b} cm', f'{b * k + a} cm']))
    def semejanza():
        h, s, S = R(2, 6), R(2, 4), R(6, 15)
        if (h * S) % s:
            return None
        return ('euclides', 'Semejanza', f'Un poste de {h} m da una sombra de {s} m. A la misma hora, un árbol da una sombra de {S} m. ¿Cuánto mide el árbol?', f'{h * S // s} m',
                distintos(f'{h * S // s} m', [f'{s * S // h if s * S % h == 0 else S + h} m', f'{S + h - s} m', f'{h * S} m']))
    def esfera():
        r = R(1, 6)
        return ('euclides', 'Volumen', f'¿Cuál es el volumen de una esfera de radio {r} cm? (V = 4/3 π r³, deje π)', f'{pi(fr(F(4 * r ** 3, 3)))} cm³',
                distintos(f'{pi(fr(F(4 * r ** 3, 3)))} cm³', [f'{pi(4 * r * r)} cm³', f'{pi(fr(F(4 * r * r, 3)))} cm³', f'{pi(r ** 3)} cm³']))
    def cono():
        r, h = R(1, 6), R(3, 9) // 3 * 3
        return ('euclides', 'Volumen', f'¿Cuál es el volumen de un cono de radio {r} cm y altura {h} cm? (V = π r² h / 3, deje π)', f'{pi(r * r * h // 3)} cm³',
                distintos(f'{pi(r * r * h // 3)} cm³', [f'{pi(r * r * h)} cm³', f'{pi(r * h // 3 if r * h % 3 == 0 else r * h)} cm³', f'{pi(2 * r * h)} cm³']))
    def distancia():
        a, b, c = random.choice([(3, 4, 5), (6, 8, 10), (5, 12, 13), (8, 6, 10)])
        x1, y1 = R(-3, 3), R(-3, 3)
        return ('euclides', 'Geometría analítica', f'¿Cuál es la distancia entre ({x1}, {y1}) y ({x1 + a}, {y1 + b})?', c, distintos(c, [a + b, c * c, abs(a - b) + 1]))
    # Bernoulli
    def permutaciones():
        n = R(3, 6)
        return ('bernoulli', 'Conteo', f'¿De cuántas formas se pueden ordenar {n} libros distintos en un estante?', math.factorial(n), distintos(math.factorial(n), [n * n, n * (n - 1), 2 ** n]))
    def combinaciones():
        n, k = random.choice([(5, 2), (6, 2), (5, 3), (6, 3), (7, 2), (8, 2)])
        r = math.comb(n, k)
        return ('bernoulli', 'Conteo', f'¿Cuántos comités de {k} personas se pueden formar con {n} personas?', r, distintos(r, [math.perm(n, k), n * k, n + k]))
    def principio():
        a, b, c = R(2, 5), R(2, 4), R(2, 3)
        return ('bernoulli', 'Conteo', f'Un menú tiene {a} sopas, {b} platos fuertes y {c} postres. ¿Cuántos almuerzos distintos (sopa, plato y postre) se pueden armar?', a * b * c, distintos(a * b * c, [a + b + c, a * b + c, (a + b) * c]))
    def media_tabla():
        return ('bernoulli', 'Estadística', 'En una tabla, 3 estudiantes sacaron 2, 5 sacaron 3 y 2 sacaron 5. ¿Cuál es el promedio?', '3,1', ['3,3', '3', '10'])
    return [sistema, pendiente, lineal_valor, cuadratica, discriminante, interes, thales, semejanza, esfera, cono, distancia,
            permutaciones, combinaciones, principio, media_tabla]


# ---------------------------------------------------------------------------- 10.º
def g10():
    ESP = {30: ('1/2', '√3/2', '√3/3'), 45: ('√2/2', '√2/2', '1'), 60: ('√3/2', '1/2', '√3')}
    def trig():
        a = random.choice([30, 45, 60])
        f = random.choice(['sen', 'cos', 'tan'])
        r = ESP[a][['sen', 'cos', 'tan'].index(f)]
        return ('newton', 'Trigonometría', f'¿Cuánto vale {f}({a}°)?', r, distintos(r, ['1/2', '√3/2', '√2/2', '√3', '1', '0'][::-1]))
    def rad():
        g = random.choice([30, 45, 60, 90, 120, 135, 150, 180, 270, 360])
        r = F(g, 180)
        txt = ('π' if r == 1 else f'{r.numerator}π' if r.denominator == 1 else (f'π/{r.denominator}' if r.numerator == 1 else f'{r.numerator}π/{r.denominator}'))
        return ('newton', 'Trigonometría', f'¿Cuántos radianes son {g}°?', txt, distintos(txt, ['π/3' if txt != 'π/3' else 'π/6', '2π' if txt != '2π' else 'π', f'{g}π', 'π/4' if txt != 'π/4' else '3π/4']))
    def identidad():
        return ('newton', 'Trigonometría', '¿A qué es igual sen²(x) + cos²(x)?', '1', ['0', 'tan(x)', '2 sen(x) cos(x)'])
    def triangulo_rect():
        h = random.choice([10, 12, 20, 8, 16])
        return ('newton', 'Trigonometría', f'En un triángulo rectángulo la hipotenusa mide {h} cm y un ángulo agudo mide 30°. ¿Cuánto mide el cateto opuesto a ese ángulo?', f'{h // 2} cm',
                distintos(f'{h // 2} cm', [f'{h} cm', f'{h // 2}√3 cm', f'{h * 2} cm']))
    def progresion_a():
        a1, d, n = R(-5, 10), R(2, 7), R(8, 20)
        an = a1 + (n - 1) * d
        return ('newton', 'Sucesiones', f'En la progresión aritmética {a1}, {a1 + d}, {a1 + 2 * d}, … ¿cuál es el término {n}?', an, distintos(an, [a1 + n * d, a1 * n, an - d * 2]))
    def progresion_g():
        a1, r, n = R(1, 3), random.choice([2, 3]), R(5, 7)
        an = a1 * r ** (n - 1)
        return ('newton', 'Sucesiones', f'En la progresión geométrica {a1}, {a1 * r}, {a1 * r * r}, … ¿cuál es el término {n}?', an, distintos(an, [a1 * r ** n, a1 * r * n, an + r]))
    def inecuacion():
        a, b, c = R(2, 6), R(-8, 8), R(-5, 15)
        if b == 0:
            return None
        x = F(c - b, a)
        return ('newton', 'Inecuaciones', f'Resuelva: {poli(a, b)} > {c}', f'x > {fr(x)}', distintos(f'x > {fr(x)}', [f'x < {fr(x)}', f'x > {fr(F(c + b, a))}', f'x > {c - b}']))
    # Euclides
    def punto_medio():
        x1, y1, x2, y2 = R(-6, 6) * 2, R(-6, 6) * 2, R(-6, 6) * 2, R(-6, 6) * 2
        m = f'({(x1 + x2) // 2}, {(y1 + y2) // 2})'
        return ('euclides', 'Geometría analítica', f'¿Cuál es el punto medio entre ({x1}, {y1}) y ({x2}, {y2})?', m, distintos(m, [f'({x1 + x2}, {y1 + y2})', f'({(x2 - x1) // 2}, {(y2 - y1) // 2})', f'({(y1 + y2) // 2}, {(x1 + x2) // 2})']))
    def recta():
        m, b = R(-4, 4), R(-6, 6)
        if m == 0:
            return None
        x0 = R(-3, 3)
        y0 = m * x0 + b
        if b == 0 or y0 == b:
            return None
        r = f'y = {poli(m, b)}'
        return ('euclides', 'Geometría analítica', f'¿Cuál es la ecuación de la recta de pendiente {m} que pasa por ({x0}, {y0})?', r,
                distintos(r, [f'y = {poli(m, y0)}', f'y = {poli(-m, b)}', f'y = {poli(b, m)}']))
    def circunferencia():
        h, k, r = R(-5, 5), R(-5, 5), R(2, 6)
        txt = f'(x {"−" if h >= 0 else "+"} {abs(h)})² + (y {"−" if k >= 0 else "+"} {abs(k)})² = {r * r}'
        return ('euclides', 'Cónicas', f'¿Cuáles son el centro y el radio de la circunferencia {txt}?', f'Centro ({h}, {k}), radio {r}',
                distintos(f'Centro ({h}, {k}), radio {r}', [f'Centro ({-h}, {-k}), radio {r}', f'Centro ({h}, {k}), radio {r * r}', f'Centro ({k}, {h}), radio {r}']))
    def ley_senos():
        return ('euclides', 'Trigonometría', 'En un triángulo, a = 10, A = 30° y B = 90°. Por la ley de los senos, ¿cuánto mide b?', '20', ['10', '5', '10√3'])
    def perpendicular():
        m = random.choice([2, 3, 4, F(1, 2), F(-2, 3), -5])
        r = fr(-1 / F(m))
        return ('euclides', 'Geometría analítica', f'Una recta tiene pendiente {fr(m)}. ¿Qué pendiente tiene una recta perpendicular a ella?', r, distintos(r, [fr(m), fr(-F(m)), fr(1 / F(m))]))
    # Bernoulli
    def desviacion():
        return ('bernoulli', 'Estadística', '¿Qué mide la desviación estándar de un conjunto de datos?', 'Qué tan dispersos están los datos respecto al promedio', ['El dato que más se repite', 'El valor central de los datos ordenados', 'La diferencia entre el mayor y el menor'])
    def condicional():
        h, m = R(10, 20), R(10, 20)
        hf, mf = R(3, h - 2), R(3, m - 2)
        p = F(mf, hf + mf)
        return ('bernoulli', 'Probabilidad', f'En un curso, {hf} hombres y {mf} mujeres juegan fútbol. Si se escoge al azar a alguien que juega fútbol, ¿cuál es la probabilidad de que sea mujer?', fr(p),
                distintos(fr(p), [fr(F(mf, h + m)), fr(F(m, h + m)), fr(F(hf, hf + mf))]))
    def contrario():
        p = random.choice([F(1, 4), F(2, 5), F(3, 10), F(1, 6), F(5, 8)])
        return ('bernoulli', 'Probabilidad', f'La probabilidad de que llueva mañana es {fr(p)}. ¿Cuál es la probabilidad de que NO llueva?', fr(1 - p), distintos(fr(1 - p), [fr(p), '1', fr(F(1, p.denominator))]))
    return [trig, rad, identidad, triangulo_rect, progresion_a, progresion_g, inecuacion, punto_medio, recta, circunferencia,
            ley_senos, perpendicular, desviacion, condicional, contrario]


# ---------------------------------------------------------------------------- 11.º
def g11():
    def log():
        b, e = random.choice([2, 3, 5, 10]), R(2, 5)
        return ('newton', 'Logaritmos', f'¿Cuánto es log en base {b} de {b ** e:,}?'.replace(',', '.'), e, distintos(e, [b ** e // b, e + 1, b * e]))
    def log_prop():
        return ('newton', 'Logaritmos', '¿A qué es igual log(a · b)?', 'log a + log b', ['log a · log b', 'log(a + b)', 'log a − log b'])
    def exponencial():
        b, e = random.choice([2, 3, 5]), R(2, 5)
        return ('newton', 'Ecuaciones exponenciales', f'Resuelva: {b}^x = {b ** e}', f'x = {e}', distintos(f'x = {e}', [f'x = {b ** e // b}', f'x = {e + 1}', f'x = {b ** e}']))
    def derivada_pot():
        a, n = R(2, 7), R(2, 5)
        r = mono(a * n, n - 1)
        return ('newton', 'Derivadas', f'¿Cuál es la derivada de f(x) = {mono(a, n)}?', r, distintos(r, [mono(a, n - 1), mono(a * n, n), mono(a + n, n - 1)]))
    def derivada_pol():
        a, b, c = R(2, 6), R(-6, 9), R(-9, 9)
        if b == 0 or c == 0:
            return None
        r = poli(2 * a, b)
        return ('newton', 'Derivadas', f'¿Cuál es la derivada de f(x) = {poli(a, b, c)}?', r, distintos(r, [poli(a, b), poli(2 * a, b, c), mono(2 * a, 2)]))
    def limite():
        a = R(1, 7)
        return ('newton', 'Límites', f'¿Cuánto es el límite cuando x → {a} de (x² − {a * a}) / (x − {a})?', 2 * a, distintos(2 * a, [0, a, a * a]))
    def limite_inf():
        a, b = R(2, 9), R(2, 9)
        r = fr(F(a, b))
        return ('newton', 'Límites', f'¿Cuánto es el límite cuando x → ∞ de ({a}x² + 1) / ({b}x² − 3)?', r, distintos(r, ['∞', '0', fr(F(-1, 3))]))
    def dominio():
        a = R(1, 9)
        return ('newton', 'Funciones', f'¿Cuál es el dominio de f(x) = √(x − {a})?', f'x ≥ {a}', distintos(f'x ≥ {a}', [f'x > {a}', f'x ≤ {a}', 'Todos los reales']))
    def compuesta():
        a, b, x = R(2, 4), R(1, 5), R(1, 4)
        r = (a * x + b) ** 2
        return ('newton', 'Funciones', f'Si f(x) = x² y g(x) = {a}x + {b}, ¿cuánto vale f(g({x}))?', r, distintos(r, [a * x * x + b, (a * x) ** 2 + b, a * (x + b) ** 2]))
    def integral():
        a, n = R(1, 5), R(1, 4)
        k = F(a, n + 1)
        coef = '' if k == 1 else (f'({fr(k)})' if k.denominator != 1 else fr(k))
        r = f'{coef}x' + ('²' if n + 1 == 2 else f'^{n + 1}') + ' + C'
        return ('newton', 'Integrales', f'¿Cuál es la integral de {mono(a, n)} dx?', r, distintos(r, [f'{mono(a * n, n - 1)} + C', f'{mono(a, n + 1)} + C', f'{mono(a + 1, n + 1)} + C']))
    # Euclides
    def maximo():
        a = R(1, 4) * 4
        return ('euclides', 'Optimización', f'Con {a} m de malla se quiere cercar un terreno rectangular de la mayor área posible. ¿Cuál es esa área?', f'{(a // 4) ** 2} m²',
                distintos(f'{(a // 4) ** 2} m²', [f'{a * a // 8} m²', f'{a} m²', f'{(a // 4) * (a // 2)} m²']))
    def parabola_vertice():
        h, k, a = R(-4, 4), R(-5, 5), random.choice([1, 2, -1])
        b, c = -2 * a * h, a * h * h + k
        txt = poli(a, b, c)
        return ('euclides', 'Cónicas', f'¿Cuál es el vértice de la parábola y = {txt}?', f'({h}, {k})', distintos(f'({h}, {k})', [f'({-h}, {k})', f'({h}, {c})', f'({k}, {h})']))
    def elipse():
        a, b = R(4, 7), R(2, 3)
        return ('euclides', 'Cónicas', f'En la elipse x²/{a * a} + y²/{b * b} = 1, ¿cuánto mide el eje mayor?', 2 * a, distintos(2 * a, [a, a * a, 2 * b]))
    def area_integral():
        return ('euclides', 'Integrales', '¿Cuál es el área bajo la recta y = 2x entre x = 0 y x = 3?', '9', ['6', '18', '3'])
    def pendiente_tangente():
        x0 = R(1, 4)
        return ('euclides', 'Derivadas', f'¿Cuál es la pendiente de la recta tangente a y = x² en el punto x = {x0}?', 2 * x0, distintos(2 * x0, [x0 * x0, x0, 2]))
    # Bernoulli
    def binomial():
        n = R(3, 5)
        p = F(1, 2 ** n)
        return ('bernoulli', 'Probabilidad', f'Se lanza una moneda {n} veces. ¿Cuál es la probabilidad de que salgan {n} caras?', fr(p), distintos(fr(p), [f'1/{n}', f'1/{2 * n}', fr(F(n, 2 ** n))]))
    def comb_cartas():
        n, k = random.choice([(10, 3), (8, 3), (7, 4), (9, 2), (12, 2)])
        return ('bernoulli', 'Conteo', f'¿De cuántas maneras se pueden escoger {k} estudiantes de un grupo de {n} para representar al colegio?', math.comb(n, k), distintos(math.comb(n, k), [math.perm(n, k), n ** k if n ** k < 10 ** 6 else n * k, n * k]))
    def independientes():
        a, b = random.choice([(F(1, 2), F(1, 3)), (F(2, 5), F(1, 2)), (F(3, 4), F(2, 3)), (F(1, 4), F(1, 5))])
        return ('bernoulli', 'Probabilidad', f'A y B son eventos independientes con P(A) = {fr(a)} y P(B) = {fr(b)}. ¿Cuánto es P(A y B)?', fr(a * b), distintos(fr(a * b), [fr(a + b) if a + b <= 1 else fr(a), fr(a + b - a * b), fr(abs(a - b)) if a != b else '0']))
    def esperanza():
        return ('bernoulli', 'Probabilidad', 'En un juego se gana $1.000 con probabilidad 1/4 y se pierde $200 con probabilidad 3/4. ¿Cuál es la ganancia esperada?', '$100', ['$800', '$250', '−$50'])
    return [log, log_prop, exponencial, derivada_pot, derivada_pol, limite, limite_inf, dominio, compuesta, integral,
            maximo, parabola_vertice, elipse, area_integral, pendiente_tangente, binomial, comb_cartas, independientes, esperanza]


def generar():
    banco = []
    for grado, fabrica in ((6, g6), (7, g7), (8, g8), (9, g9), (10, g10), (11, g11)):
        plantillas = fabrica()
        def categoria(f):
            for _ in range(200):
                q = f()
                if q:
                    return q[0]
            return ''
        cats = {f: categoria(f) for f in plantillas}
        por_cat = {k: [f for f in plantillas if cats[f] == k] for k in CUPO}
        vistas, cuenta = set(), {k: 0 for k in CUPO}
        for cat, cupo in CUPO.items():
            fs = por_cat[cat]
            intentos = 0
            while cuenta[cat] < cupo and intentos < 5000:
                q = fs[intentos % len(fs)]()          # en turno: cada plantilla sale más o menos igual
                intentos += 1
                if not q:
                    continue
                c, tema, texto, correcta, malas = q
                correcta = str(correcta)
                malas = [str(m) for m in malas][:3]
                if texto in vistas or len(set(malas + [correcta])) != 4:
                    continue
                vistas.add(texto)
                opciones = [{'texto': correcta, 'correcta': True}] + [{'texto': m, 'correcta': False} for m in malas]
                random.shuffle(opciones)
                banco.append({'grado': grado, 'ciclo': NIVEL[grado], 'categoria': c, 'tema': tema, 'texto': texto, 'opciones': opciones,
                              'origen': f'Banco olimpiada {grado}.º'})
                cuenta[cat] += 1
            if cuenta[cat] < cupo:
                raise SystemExit(f'Grado {grado}: solo {cuenta[cat]} preguntas de {cat}')
    return banco


if __name__ == '__main__':
    banco = generar()
    ruta = os.path.join(os.path.dirname(__file__), 'olimpiada_6_11.json')
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(banco, f, ensure_ascii=False, indent=0)
    from collections import Counter
    print(len(banco), 'preguntas ·', dict(Counter((p['grado'], p['categoria']) for p in banco)))
