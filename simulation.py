"""
Simulação de Fila com Dois Servidores usando SimPy
Baseado em: Trabalho 1 - Modelagem e Simulação
"""

import random
import sys
from collections import defaultdict

import simpy

# ==================== CONFIGURAÇÕES DO SISTEMA ====================

INTERARRIVAL_DISTRIBUTION = {
    1: 0.25,
    2: 0.40,
    3: 0.20,
    4: 0.15
}

FUNC1_SERVICE_DISTRIBUTION = {
    2: 0.30,
    3: 0.28,
    4: 0.25,
    5: 0.17
}

FUNC2_SERVICE_DISTRIBUTION = {
    3: 0.35,
    4: 0.25,
    5: 0.20,
    6: 0.20
}

DEBUG = True

# ==================== CLASSES DO SISTEMA ====================

class Server:
    def __init__(self, env, name, service_distribution):
        self.env = env
        self.name = name
        self.service_distribution = service_distribution
        self.service_count = 0
        
    def get_service_time(self):
        return random.choices(
            list(self.service_distribution.keys()),
            weights=list(self.service_distribution.values()),
            k=1
        )[0]


class SimulationResults:
    def __init__(self):
        self.customers_data = []
    
    def add_customer_data(self, customer_id, arrival_time, start_service, 
                          service_time, departure_time, wait_time, server_name):
        self.customers_data.append({
            'id': customer_id,
            'arrival': arrival_time,
            'start_service': start_service,
            'service_time': service_time,
            'departure': departure_time,
            'wait_time': wait_time,
            'queue_time': start_service - arrival_time,
            'server': server_name
        })
    
    def print_results(self, total_time):
        print("\n" + "="*90)
        print("RESULTADOS DA SIMULAÇÃO DE FILA COM DOIS SERVIDORES")
        print("="*90)
        
        total_customers = len(self.customers_data)
        print(f"\nTotal de clientes simulados: {total_customers}")
        print(f"Tempo total de simulação: {total_time:.2f} minutos")
        
        # ---------------------------------------------------------
        # Basic Statistics
        # ---------------------------------------------------------
        print("\n" + "-"*90)
        print("ESTATÍSTICAS GERAIS DE ESPERA E ATENDIMENTO")
        print("-"*90)
        
        wait_times = [c['wait_time'] for c in self.customers_data]
        service_times = [c['service_time'] for c in self.customers_data]
        total_times = [c['departure'] - c['arrival'] for c in self.customers_data]
        
        if wait_times:
            print(f"Tempo médio de espera na fila: {sum(wait_times)/len(wait_times):.2f} minutos")
            print(f"Tempo máximo de espera na fila: {max(wait_times):.2f} minutos")
        
        clients_with_wait = sum(1 for w in wait_times if w > 0.001)
        print(f"Clientes que precisaram aguardar: {clients_with_wait} de {len(wait_times)} ({100*clients_with_wait/len(wait_times):.1f}%)")
        
        if clients_with_wait > 0:
            wait_with_queue = [w for w in wait_times if w > 0.001]
            print(f"Tempo médio de espera (apenas dos que esperaram): {sum(wait_with_queue)/len(wait_with_queue):.2f} minutos")
        
        if service_times:
            print(f"\nTempo médio de serviço global: {sum(service_times)/len(service_times):.2f} minutos")
        if total_times:
            print(f"Tempo médio total no sistema (fila + serviço): {sum(total_times)/len(total_times):.2f} minutos")
        
        # ---------------------------------------------------------
        # Server Specific & Dimensioning Statistics
        # ---------------------------------------------------------
        print("\n" + "-"*90)
        print("MÉTRICAS DE DIMENSIONAMENTO E OCUPAÇÃO (CAPACITY PLANNING)")
        print("-"*90)
        
        servers_count = defaultdict(int)
        servers_busy = defaultdict(float)
        
        for c in self.customers_data:
            servers_count[c['server']] += 1
            servers_busy[c['server']] += c['service_time']

        throughput = total_customers / total_time if total_time > 0 else 0
        print(f"Vazão do Sistema (Throughput): {throughput:.3f} clientes/minuto")
        
        avg_customers_system = throughput * (sum(total_times)/len(total_times))
        avg_customers_queue = throughput * (sum(wait_times)/len(wait_times))
        print(f"Média de clientes no sistema (L): {avg_customers_system:.2f} clientes")
        print(f"Média de clientes na fila (Lq): {avg_customers_queue:.2f} clientes\n")

        for server_name in sorted(servers_count.keys()):
            busy_time = servers_busy[server_name]
            utilization = (busy_time / total_time) * 100 if total_time > 0 else 0
            avg_service = busy_time / servers_count[server_name] if servers_count[server_name] > 0 else 0
            
            print(f"[{server_name}]")
            print(f"  - Clientes atendidos: {servers_count[server_name]}")
            print(f"  - Tempo médio de atendimento: {avg_service:.2f} minutos")
            print(f"  - Taxa de Ocupação (Utilização): {utilization:.1f}%")
        
        # ---------------------------------------------------------
        # Detailed Log
        # ---------------------------------------------------------
        print("\n" + "-"*90)
        print("TABELA DETALHADA DE CLIENTES")
        print("-"*90)
        print(f"{'ID':<5} {'Chegada':<10} {'Início':<10} {'Duração':<10} {'Saída':<10} {'Espera':<10} {'Servidor':<10}")
        print("-"*90)
        
        for c in self.customers_data:
            print(f"{c['id']:<5.0f} {c['arrival']:<10.2f} {c['start_service']:<10.2f} {c['service_time']:<10.2f} "
                  f"{c['departure']:<10.2f} {c['wait_time']:<10.2f} {c['server']:<10}")
        print("="*90)


# ==================== FUNÇÕES DE GERAÇÃO DE VALORES ====================

def get_interarrival_time():
    return random.choices(
        list(INTERARRIVAL_DISTRIBUTION.keys()),
        weights=list(INTERARRIVAL_DISTRIBUTION.values()),
        k=1
    )[0]


# ==================== PROCESSOS DA SIMULAÇÃO ====================

def customer_process(env, customer_id, arrival_time, server_store, results):
    if DEBUG:
        print(f"[{env.now:.2f}] Cliente {customer_id} chegou")
    
    arrival = env.now
    
    # Request a server from the PriorityStore. 
    # If both are available, Priority 0 (Func1) is popped first.
    store_item = yield server_store.get()
    server = store_item.item
    
    start_service = env.now
    wait_time = start_service - arrival
    
    if DEBUG:
        print(f"[{env.now:.2f}] Cliente {customer_id} começou atendimento com {server.name} (esperou {wait_time:.2f} min)")
    
    service_time = server.get_service_time()
    
    yield env.timeout(service_time)
    
    departure_time = env.now
    
    if DEBUG:
        print(f"[{env.now:.2f}] Cliente {customer_id} terminou atendimento com {server.name}")
    
    results.add_customer_data(
        customer_id, arrival, start_service, service_time, 
        departure_time, wait_time, server.name
    )
    
    server.service_count += 1
    
    # Return the server back to the PriorityStore so the next in line can use it
    priority = 0 if server.name == "Func1" else 1
    server_store.put(simpy.PriorityItem(priority, server))


def customer_generator(env, server_store, num_customers, results):
    print(f"\n[Gerador] Iniciando geração de {num_customers} clientes...")
    
    for i in range(1, num_customers + 1):
        interarrival = get_interarrival_time()
        yield env.timeout(interarrival)
        
        if DEBUG:
            print(f"[{env.now:.2f}] Próximo cliente será o {i+1}")
        
        env.process(customer_process(env, i, env.now, server_store, results))
    
    print(f"\n[Gerador] Todos os {num_customers} clientes foram gerados")


# ==================== FUNÇÃO PRINCIPAL ====================

def run_simulation(num_customers=26, seed=None):
    if seed is not None:
        random.seed(seed)
    
    print(f"\n{'='*90}")
    print("SIMULAÇÃO DE FILA COM DOIS SERVIDORES")
    print(f"{'='*90}")
    print(f"Número de clientes: {num_customers}")
    print(f"{'='*90}\n")
    
    env = simpy.Environment()
    results = SimulationResults()
    
    print("[Setup] Criando servidores...")
    func1 = Server(env, "Func1", FUNC1_SERVICE_DISTRIBUTION)
    func2 = Server(env, "Func2", FUNC2_SERVICE_DISTRIBUTION)
    
    # PriorityStore implementation for queue handling
    server_store = simpy.PriorityStore(env, capacity=2)
    # Give Func1 priority 0 (higher priority) and Func2 priority 1
    server_store.put(simpy.PriorityItem(0, func1))
    server_store.put(simpy.PriorityItem(1, func2))
    
    print("[Setup] Func1 e Func2 criados na PriorityStore")
    
    print("[Setup] Iniciando gerador de clientes...")
    env.process(customer_generator(env, server_store, num_customers, results))
    
    print("[Simulação] Executando...\n")
    env.run()
    
    print("\n[Simulação] Simulação terminada!")
    
    if results.customers_data:
        total_time = max(c['departure'] for c in results.customers_data)
    else:
        total_time = 0
    
    results.print_results(total_time)
    
    return results, [func1, func2], total_time


def main():
    num_customers = 26
    
    if len(sys.argv) > 1:
        try:
            num_customers = int(sys.argv[1])
        except ValueError:
            print(f"Número inválido de clientes: '{sys.argv[1]}'. Usando padrão ({num_customers}).")
    
    run_simulation(num_customers=num_customers)


if __name__ == "__main__":
    main()

