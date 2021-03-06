from godfather.roles.mixins import SingleAction, Shooter, MafiaMember

DESCRIPTION = 'You may shoot someone every night.'


class Goon(MafiaMember, Shooter, SingleAction):
    """
    A member of organized crime, trying to work their way to the top.

    - Win Condition: Kill anyone that will not submit to the Mafia.

    + Abilities:
    + You can choose to attack if the Godfather doesn't give orders.
    + If the Godfather dies, you will become the next Godfather.
    """
    name = 'Goon'
    description = DESCRIPTION
    unique = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.categories.append('Mafia Killing')

    async def on_pm_command(self, ctx, game, player, args):
        if any(filter(lambda action: action['player'].role.name == 'Godfather', game.night_actions)):
            return await ctx.send('The Godfather has ordered you to shoot someone.')
        await super().on_pm_command(ctx, game, player, args)

    async def tear_down(self, actions, player, target):

        record = actions.record[target.user.id]['nightkill']
        success = record['result'] and player in record['by']

        if not success:
            return await player.user.send('Your target was too strong to kill!')
        await target.user.send('You were shot by a Goon. You have died!')

    def can_do_action(self, game):
        if game.setup.name == 'dethy' and game.cycle == 1:
            return False, 'You cannot shoot N1 in Dethy.'
        return super().can_do_action(game)
