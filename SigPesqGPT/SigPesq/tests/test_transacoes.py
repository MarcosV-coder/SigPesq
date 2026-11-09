import unittest
from unittest.mock import patch,MagicMock
from decimal import Decimal
import db
import repositorio


class TransacoesTest(unittest.TestCase):
    def setUp(self):
        self.conn=MagicMock()
        self.cur=self.conn.cursor.return_value
        self.patcher=patch('db.mysql.connector.connect',return_value=self.conn)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_commit_e_fechamento(self):
        with db.transacao() as cur:
            cur.execute('SELECT %s',(1,))
        self.conn.commit.assert_called_once()
        self.conn.rollback.assert_not_called()
        self.cur.close.assert_called_once()
        self.conn.close.assert_called_once()

    def test_rollback_em_falha(self):
        with self.assertRaises(ValueError):
            with db.transacao():
                raise ValueError('Falha em uma gravação relacionada')
        self.conn.rollback.assert_called_once()
        self.conn.commit.assert_not_called()
        self.conn.close.assert_called_once()

    def test_alocacao_acima_do_contrato_nao_grava(self):
        self.cur.fetchone.side_effect=[{'valor_total':Decimal('100.00')},{'total':Decimal('80.00')}]
        with self.assertRaisesRegex(ValueError,'ultrapassa'):
            repositorio.salvar('alocacoes',{'codigo_projeto':1,'codigo_financiamento':2,'valor_destinado':Decimal('30')})
        self.conn.rollback.assert_called_once()
        self.assertFalse(any('INSERT' in call.args[0] for call in self.cur.execute.call_args_list))

    def test_texto_sql_e_parametro(self):
        payload="Projeto'); DROP TABLE projeto; --"
        repositorio.salvar('financiamentos',dict(codigo_financiamento=1,agencia_financiadora='cnpq',
            tipo_fomento='auxilio',valor_total=Decimal('100'),data_inicio='2026-01-01',data_termino='2027-01-01'))
        db.executar('SELECT %s',(payload,))
        self.assertEqual(self.cur.execute.call_args.args,('SELECT %s',(payload,)))


if __name__=='__main__':
    unittest.main()
