"""Fase 2: entrypoint. Sem IA, sem banco. (--chat so na Fase 5.)"""
import argparse

from src import config, monitor, organizador


def _resumo(resultado):
    for mov in resultado["movimentos"]:
        prefixo = "[dry-run]" if resultado["dry_run"] else f"[{mov['status']}]"
        print(f"{prefixo} {mov['origem']} -> {mov['destino']}")
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
    ap.add_argument("--chat", action="store_true", help="conversa com o organizador")
    args = ap.parse_args(argv)

    if args.chat:
        from src import chat as chat_mod
        chat_mod.iniciar()
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
        monitor.iniciar(dry_run=args.dry_run)
        return 0
    resultado = organizador.processar(dry_run=args.dry_run)
    _resumo(resultado)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
