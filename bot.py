# SOLO CAMBIO: TOKEN POR VARIABLE
def main():
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    # Añadir comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cc", mostrar_datos_cedula))
    application.add_handler(CommandHandler("nombres", mostrar_datos_nombres))
    application.add_handler(CommandHandler("c2", comando_c2))
    application.add_handler(CommandHandler("placa", comando_placa))
    application.add_handler(CommandHandler("llave", comando_llave))
    application.add_handler(CommandHandler("nequi", comando_nequi))
    application.add_handler(CommandHandler("generar_key", generar_key))
    application.add_handler(CommandHandler("redeem", redeem))
    application.add_handler(CommandHandler("eliminar_key", eliminar_key))
    application.add_handler(CommandHandler("addadmin", add_admin))
    application.add_handler(CommandHandler("listkey", ver_claves_admin))
    application.add_handler(CommandHandler("info", ver_info_usuario))
    application.add_handler(CommandHandler("heidysql", heidysql))

    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, registrar_usuario)
    application.add_handler(message_handler)

    logger.info("Bot iniciado y listo para recibir comandos.")
    application.run_polling()