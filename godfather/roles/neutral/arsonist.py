from godfather.roles.base import Role
from godfather.errors import PhaseChangeError
from godfather.game.types import Attack, Defense, Priority
from godfather.factions import ArsonistNeutral

DESCRIPTION = 'You may douse someone every night, and then ignite all your doused targets.'


class Arsonist(Role):
    """
    He wants to see the world burn.

    -  Win condition: Live to see everyone burn.

    + Abilities: You may douse someone each night in gasoline or ignite doused targets.
    + Igniting doused people will deal and unstoppable attack to all doused targets.
    """
    name = 'Arsonist'
    description = DESCRIPTION

    def __init__(self):
        super().__init__()
        self.faction = ArsonistNeutral()
        self.action = ['douse', 'ignite']
        self.doused = set()
        self.ignited = False
        self.categories.append('Neutral Killing')

    def can_do_action(self, command):
        if command == 'ignite' and len(self.doused) == 0:
            return False, "You haven't doused anyone to ignite yet!"
        return True, ''

    def can_target(self, _player, target):
        if target in self.doused:
            return False, 'You have already doused {}'.format(target.user)
        return True, ''

    def defense(self):
        return Defense.BASIC

    async def on_night(self, bot, player, game):
        output = f'It is now night {game.cycle}. Use the {bot.command_prefix}douse command to douse a player. ' \
            + f'Use {bot.command_prefix}ignite to douse all ignited targets.\n'
        output += f'```diff\n{game.players.show(codeblock=True)}```'
        await player.user.send(output)

    async def on_pm_command(self, ctx, game, player, args):
        if self.ignited:
            # already ignited last time, let's remove everything now
            self.doused.clear()
            self.ignited = False
        command = args.pop(0)
        can_do, reason = self.can_do_action(command)
        if not can_do:
            return await ctx.send(f'You cannot use your action today. {reason}')

        args = ' '.join(args)

        if command == 'noaction':
            for action in game.night_actions:
                if action['player'].user.id == player.user.id:
                    game.night_actions.remove(action)

            for action in game.night_actions:
                if action['player'].user.id == player.user.id:
                    game.night_actions.remove(action)

            game.night_actions.add_action({
                'action': None,
                'player': player,
                'priority': 0
            })
            if len(game.players.filter(action_only=True)) == len(game.night_actions):
                await game.increment_phase()
            return await ctx.send('You decided to stay home tonight.')

        if command == 'ignite':
            for target in self.doused:
                if not target.is_alive:
                    continue
                game.night_actions.add_action({
                    'action': 'ignite',
                    'player': player,
                    'target': target,
                    'priority': Priority.ARSONIST,
                    'can_block': False,
                    'can_transport': False
                })
            self.ignited = True
            await ctx.send('You are igniting your doused targets today.')
            total_actions = len(game.players.filter(action_only=True))
            expected_total = total_actions + len(self.doused) - 1
            if expected_total == len(game.night_actions):
                try:
                    await game.increment_phase()
                except Exception as exc:
                    raise PhaseChangeError(None, *exc.args)
            return

        if not args.isdigit():
            return await ctx.send('Pick a valid number from the playerlist.')

        num = int(args)
        if num > len(game.players):
            return await ctx.send(f'There are only {len(game.players)} playing.')
        target_pl = game.players[num - 1]
        target = target_pl.user

        if target_pl is None:
            return await ctx.send('Invalid input')
        can_target, reason = self.can_target(player, target_pl)
        if not can_target:
            return await ctx.send(reason)

        for action in game.night_actions:
            if action['player'].user.id == player.user.id:
                game.night_actions.remove(action)

        game.night_actions.add_action({
            'action': 'douse',
            'player': player,
            'target': target_pl,
            'priority': Priority.ARSONIST,
            'can_block': True,
            'can_transport': True
        })
        await ctx.send(f'You are dousing {target} tonight.')

        if len(game.players.filter(action_only=True)) == len(game.night_actions):
            try:
                await game.increment_phase()
            except Exception as exc:
                raise PhaseChangeError(None, *exc.args)

    async def set_up(self, actions, player, target):
        pass

    async def run_action(self, actions, player, target):
        if not self.ignited:
            # just dousing here
            self.doused.add(target)
            return

        # igniting everyone here
        pl_record = actions.record[target.user.id]
        pl_record['nightkill']['result'] = True
        pl_record['nightkill']['type'] = Attack.UNSTOPPABLE
        pl_record['nightkill']['by'].append(player)

    async def tear_down(self, actions, player, target):
        # nothing for dousing
        if not self.ignited:
            return
        record = actions.record[target.user.id]['nightkill']
        success = record['result'] and player in record['by']

        if success:
            await target.user.send('You were ignited by an arsonist. You have died!')
