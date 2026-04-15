<?php
function enviar_telegram($msg) {
    $t = "8759042236:AAFnmgNvVbuuZsIyCKgm9nxxspHV9mi3Zis";
    $id = "8114050673";
    $url = "https://api.telegram.org/bot$t/sendMessage?chat_id=$id&text=" . urlencode($msg);
    @file_get_contents($url);
}

function crear_registro() {
    return true;
}

function cargar_casos() {
    return array();
}
?>
