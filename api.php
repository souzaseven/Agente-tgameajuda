<?php
// API simulada para frontend estático HostGator
header('Content-Type: application/json');

$rota = isset($_GET['rota']) ? $_GET['rota'] : '';
$method = $_SERVER['REQUEST_METHOD'];

if ($rota === 'intro' && $method === 'GET') {
    echo json_encode([
        'text' => 'tgameajuda agente ativado — seu copiloto de help desk, pronto para agilizar atendimentos, análise de tickets e comunicação.\n\nCom o que posso ajudar agora?'
    ]);
    exit;
}

if ($rota === 'chat' && $method === 'POST') {
    $input = json_decode(file_get_contents('php://input'), true);
    $msg = isset($input['message']) ? $input['message'] : '';
    // Simulação de resposta
    $resposta = 'Recebido: ' . htmlspecialchars($msg);
    echo json_encode([
        'text' => $resposta,
        'tools_used' => []
    ]);
    exit;
}

if ($rota === 'status' && $method === 'GET') {
    echo json_encode([
        'model' => 'php-mock',
        'max_tokens' => 8192,
        'turns_in_history' => 0,
        'max_history_turns' => 20,
        'tools_available' => ['simulado']
    ]);
    exit;
}

http_response_code(404);
echo json_encode(['detail' => 'Rota não encontrada']);
