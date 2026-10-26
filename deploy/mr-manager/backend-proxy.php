<?php
/**
 * Forward /api/* to local Gunicorn (mod_proxy [P] is disabled on this vhost).
 */
declare(strict_types=1);

$backend = 'http://127.0.0.1:34568';
$uri = $_SERVER['REQUEST_URI'] ?? '/';
$url = $backend . $uri;

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
$body = file_get_contents('php://input');

$headers = ['Host: ' . ($_SERVER['HTTP_HOST'] ?? 'mr-manager.ru')];
if (!empty($_SERVER['CONTENT_TYPE'])) {
    $headers[] = 'Content-Type: ' . $_SERVER['CONTENT_TYPE'];
}
$skip = ['host', 'connection', 'content-length', 'transfer-encoding', 'content-type'];
foreach ($_SERVER as $key => $value) {
    if (!str_starts_with($key, 'HTTP_')) {
        continue;
    }
    $name = str_replace('_', '-', substr($key, 5));
    if (in_array(strtolower($name), $skip, true)) {
        continue;
    }
    $headers[] = $name . ': ' . $value;
}
if ($body !== '') {
    $headers[] = 'Content-Length: ' . strlen($body);
}

$ch = curl_init($url);
curl_setopt_array($ch, [
    CURLOPT_CUSTOMREQUEST => $method,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_HEADER => true,
    CURLOPT_HTTPHEADER => $headers,
    CURLOPT_POSTFIELDS => $body !== '' ? $body : null,
    CURLOPT_TIMEOUT => 120,
]);

$response = curl_exec($ch);
if ($response === false) {
    http_response_code(502);
    header('Content-Type: application/json');
    echo json_encode(['detail' => 'Backend unavailable']);
    exit;
}

$status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$headerSize = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
curl_close($ch);

$rawHeaders = substr($response, 0, $headerSize);
$bodyOut = substr($response, $headerSize);

http_response_code($status);
foreach (explode("\r\n", $rawHeaders) as $line) {
    if ($line === '' || stripos($line, 'HTTP/') === 0) {
        continue;
    }
    if (stripos($line, 'transfer-encoding:') === 0) {
        continue;
    }
    header($line, false);
}

echo $bodyOut;
