<?php
$sid = "ACf4956e3782c9b2f178f010425f491ce5";
$token = "f434ab456ffbe67f9718782663d89267";
$from = "whatsapp:+14155238886"; // Twilio Sandbox

$to = isset($_GET['phone']) ? "whatsapp:+" . $_GET['phone'] : "";
$body = isset($_GET['message']) ? $_GET['message'] : "رسالة فارغة";

if ($to == "") {
    echo "رقم الهاتف غير موجود.";
    exit;
}

$url = "https://api.twilio.com/2010-04-01/Accounts/$sid/Messages.json";

$data = [
    'From' => $from,
    'To' => $to,
    'Body' => $body
];

$options = [
    'http' => [
        'header'  => "Authorization: Basic " . base64_encode("$sid:$token") . "\r\n" .
                     "Content-type: application/x-www-form-urlencoded\r\n",
        'method'  => 'POST',
        'content' => http_build_query($data)
    ]
];

$context = stream_context_create($options);
$result = file_get_contents($url, false, $context);
echo $result;
?>