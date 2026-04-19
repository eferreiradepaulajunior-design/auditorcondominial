# Detecção de Anomalias Financeiras

## Padrões a detectar

### 1. Pagamentos duplicados
- Mesmo fornecedor, mesmo valor, mesmo mês
- Parcelas sequenciais pagas no mesmo período (ex: parcelas 11 e 12/12 no mesmo mês)

### 2. Variações atípicas
- Despesa que varia mais de 30% em relação à média dos 3 meses anteriores
- Conta de utilidade (água, energia) com variação acima de 20%

### 3. Fornecedores suspeitos
- Pagamentos a CPF sem contrato registrado
- Fornecedor novo com valor alto na primeira transação
- Mesmo serviço sendo pago a fornecedores diferentes

### 4. Saldo negativo
- Dois meses consecutivos com saldo negativo é crítico
- Uso de fundo de reserva para cobrir despesas ordinárias

### 5. Contas inativas
- Contas bancárias com saldo parado sem movimentação
- Conta de gestão anterior ainda ativa
