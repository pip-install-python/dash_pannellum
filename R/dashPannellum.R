# AUTO GENERATED FILE - DO NOT EDIT

#' @export
dashPannellum <- function(id=NULL, autoLoad=NULL, currentScene=NULL, customControls=NULL, height=NULL, multiRes=NULL, pitch=NULL, showCenterDot=NULL, tour=NULL, video=NULL, width=NULL, yaw=NULL) {
    
    props <- list(id=id, autoLoad=autoLoad, currentScene=currentScene, customControls=customControls, height=height, multiRes=multiRes, pitch=pitch, showCenterDot=showCenterDot, tour=tour, video=video, width=width, yaw=yaw)
    if (length(props) > 0) {
        props <- props[!vapply(props, is.null, logical(1))]
    }
    component <- list(
        props = props,
        type = 'DashPannellum',
        namespace = 'dash_pannellum',
        propNames = c('id', 'autoLoad', 'currentScene', 'customControls', 'height', 'multiRes', 'pitch', 'showCenterDot', 'tour', 'video', 'width', 'yaw'),
        package = 'dashPannellum'
        )

    structure(component, class = c('dash_component', 'list'))
}
