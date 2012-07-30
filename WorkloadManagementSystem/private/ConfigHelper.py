from DIRAC import S_OK, S_ERROR
from DIRAC.FrameworkSystem.Client.ProxyManagerClient import gProxyManager
from DIRAC.ConfigurationSystem.Client.Helpers import Registry, Operations
from DIRAC.Core.Security import Properties


def findGenericPilotCredentials( vo = False. group = False ):
  if not group and not vo:
    return S_ERROR( "Need a group or a VO to determine the Generic pilot credentials" )
  if not vo:
    vo = Registry.getVOForGroup( group )
    if not vo:
      return S_ERROR( "Group %s does not have a VO associated" % group )
  opsHelper = Operations.Operations( vo = vo )
  pilotGroup = opsHelper.getValue( "Pilot/GenericGroup", "" )
  pilotDN = opsHelper.getValue( "Pilot/GenericDN", "" )
  if pilotDN and pilotGroup:
    result = gProxyManager.userHasProxy( pilotDN, pilotGroup, 86400 )
    if not result[ 'OK' ]:
      return S_ERROR( "%s@%s has no proxy uploaded to the ProxyManager" )
    return S_OK( ( pilotDN, pilotGroup ) )
  #Auto discover
  if pilotGroup:
    pilotGroups = [ pilotGroup ]
  else:
    result = Registry.getGroupsWithProperty( Properties.GENERIC_PILOT )
    if not result[ 'OK' ]:
      return result
    pilotGroups = []
    groups = result[ 'Value' ]
    if not groups:
      return S_ERROR( "No group with %s property defined" % Properties.GENERIC_PILOT )
    result = Registry.getGroupsForVO( vo )
    if not result[ 'OK' ]:
      return result
    for voGroup in result[ 'Value' ]:
      if voGroup in groups:
        pilotGroups.append( voGroup )
  if not pilotGroups:
    return S_ERROR( "No group for VO %s is a generic pilot group" % vo )
  for pilotGroup in pilotGroups:
    DNs = Registry.getDNsInGroup( pilotGroup )
    if not DNs:
      continue
    if pilotDN:
      if pilotDN not in DNs:
        continue
      result = gProxyManager.userHasProxy( pilotDN, pilotGroup, 86400 )
      if result[ 'OK' ] and result[ 'Value' ]:
        return S_OK( ( pilotDN, pilotGroup ) )
    else:
      for DN in DNs:
        result = gProxyManager.userHasProxy( DN, pilotGroup, 86400 )
        if result[ 'OK' ] and result[ 'Value' ]:
          return S_OK( ( DN, pilotGroup ) )

  if pilotDN:
    return S_ERROR( "DN %s does not have group %s" % ( pilotDN, pilotGroups ) )
  return S_ERROR( "No generic proxy in the Proxy Manager with groups %s" % pilotGroups )


