"""Fase 2: entrypoint. Sem IA, sem banco. (--chat so na Fase 5.)"""
import argparse

from src import config, monitor, organizador


def _resumo(resultado):
    for mov in resultado["movimentos"]:
        prefixo = "[dry-run]" if resultado["dry_run"] else f"[{mov['status']}]"
        nota = f" ({mov['nota']})" if mov.get("nota") else ""
        print(f"{prefixo} {mov['origem']} -> {mov['destino']}{nota}")
    for ign in resultado["ignorados"]:
        print(f"[ignorado:{ign['motivo']}] {ign['origem']}")
    if resultado["id"]:
        print(f"log: exec_{resultado['id']}.json")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="organizaia", description="OrganizaIA - Fase 2")
    ap.add_argument("--once", action="store_true", help="varre entrada/ uma vez")
    ap.add_argument("--watch", action="store_true", help="observa entrada/ continuously")
    ap.add_argument("--dry-run", action="store_true", help="mostra sem mover")
    ap.add_argument("--desfazer", action="store_true", help="desfaz a ultima execucao")
    ap.add_argument("--modo", choices=["tipo", "ia"], default="tipo",
                    help="tipo: so regras; ia: conteudo via Gemini (padrao: tipo)")
    ap.add_argument("--chat", action="store_true", help="conversa com o organizador")
    ap.add_argument("--exportar", metavar="DESTINO.zip", help="exporta backup (banco+manifest)")
    ap.add_argument("--importar", metavar="BACKUP.zip", help="importa backup")
    ap.add_argument("--reindexar", action="store_true", help="reindexa caminhos ao importar")
    args = ap.parse_args(argv)

    if args.chat:
        from src import chat as chat_mod
        chat_mod.iniciar()
        return 0
    if args.exportar:
        from src import backup as backup_mod
        resultado = backup_mod.exportar_backup(args.exportar)
        print(f"backup: {resultado['zip']}")
        for nome in resultado["arquivos"]:
            print(f"  + {nome}")
        return 0
    if args.importar:
        import sys as _sys

        from src import backup as backup_mod
        reindexar = args.reindexar
        if not reindexar and _sys.stdin.isatty():
            reindexar = input("reindexar caminhos para esta maquina? (s/n): ").strip().lower() == "s"
        resultado = backup_mod.importar_backup(args.importar, reindexar=reindexar)
        print(f"restaurado em: {resultado['base']}")
        for nome in resultado["arquivos"]:
            print(f"  + {nome}")
        return 0

    if args.desfazer:
        resultado = organizador.desfazer_ultima_execucao(config.LOGS_DIR)
        if not resultado["restaurados"]:
            print("nada a desfazer")
        for item in resultado["restaurados"]:
            print(f"[desfeito] {item['de']} -> {item['para']}")
        return 0
    if args.watch:
        print(f"observando {config.ENTRADA_DIR} (Ctrl+C para sair)")
        monitor.iniciar(dry_run=args.dry_run, modo=args.modo)
        return 0
    resultado = organizador.processar(dry_run=args.dry_run, modo=args.modo)
    for aviso in resultado.get("avisos", []):
        print(f"[aviso] {aviso}")
    _resumo(resultado)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
