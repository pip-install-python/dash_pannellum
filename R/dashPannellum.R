# AUTO GENERATED FILE - DO NOT EDIT

#' @export
dashPannellum <- function(id=NULL, currentScene=NULL, customControls=NULL, height=NULL, loaded=NULL, multiRes=NULL, pitch=NULL, showCenterDot=NULL, tour=NULL, video=NULL, width=NULL, yaw=NULL) {
    
    props <- list(id=id, currentScene=currentScene, customControls=customControls, height=height, loaded=loaded, multiRes=multiRes, pitch=pitch, showCenterDot=showCenterDot, tour=tour, video=video, width=width, yaw=yaw)
    if (length(props) > 0) {
        props <- props[!vapply(props, is.null, logical(1))]
    }
    component <- list(
        props = props,
        type = 'DashPannellum',
        namespace = 'dash_pannellum',
        propNames = c('id', 'currentScene', 'customControls', 'height', 'loaded', 'multiRes', 'pitch', 'showCenterDot', 'tour', 'video', 'width', 'yaw'),
        package = 'dashPannellum'
        )

    structure(component, class = c('dash_component', 'list'))
}
