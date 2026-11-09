import unittest
from datetime import date
from decimal import Decimal
from validacao import moeda,data,cpf_limpo,validar
from telas.modelos import MODELOS


class ValidacaoTest(unittest.TestCase):
    def test_valores_grandes_sem_float(self):
        self.assertEqual(moeda('999.999.999.999.999.999,99'),Decimal('999999999999999999.99'))
        self.assertEqual(moeda('R$ 1.234,56'),Decimal('1234.56'))
        self.assertEqual(moeda('1234.5'),Decimal('1234.50'))

    def test_rejeita_valores_ambiguos_e_invalidos(self):
        for texto in ['1.234','1,234','0','-1','NaN','1e5','1000000000000000000','1.23,45']:
            with self.subTest(texto=texto),self.assertRaises(ValueError):
                moeda(texto)

    def test_datas_reais(self):
        self.assertEqual(data('29/02/2024'),date(2024,2,29))
        self.assertEqual(data('2026-11-08'),date(2026,11,8))
        for texto in ['29/02/2025','31/04/2026','08/11/0008']:
            with self.assertRaises(ValueError):
                data(texto)

    def test_cpf_mantem_zeros(self):
        self.assertEqual(cpf_limpo('000.000.000-01'),'00000000001')
        with self.assertRaises(ValueError):
            cpf_limpo('abc00000000001')

    def test_periodo_invertido_e_limite_titulo(self):
        campos=MODELOS['projetos']['campos']
        d=dict(codigo_projeto='1',titulo='Pesquisa',descricao='',data_inicio='02/03/2026',
               data_termino='01/03/2026',situacao='em_andamento',coordenador='00000000001')
        with self.assertRaisesRegex(ValueError,'término'):
            validar(campos,d)
        d.update(data_termino='',titulo='a'*101)
        with self.assertRaisesRegex(ValueError,'100'):
            validar(campos,d)

    def test_vinculo_inicial_exige_papel_e_data(self):
        d=dict(nome='Ana Silva',email='ana@example.invalid',cpf='00000000001',
               tipo_participante='discente',projeto=1,funcao=None,inicio='',fim='')
        with self.assertRaisesRegex(ValueError,'função'):
            validar(MODELOS['participantes']['campos'],d)


if __name__=='__main__':
    unittest.main()
