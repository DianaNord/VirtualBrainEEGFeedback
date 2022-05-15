using UnityEngine;

/// <summary>
/// Creates connections between scripts and objects for invoked events.
/// </summary>
public class ObjectsController : MonoBehaviour
{
    public GameObject fixationCross;
    public GameObject arrowLeft;
	public GameObject arrowRight;
	public GameObject brain;
    public GameObject glow;

    internal LSLFeedbackStream feedbackStream;
    internal LSLMarkerStream markerStream;
    internal TextureColorController textureController;

    /// <summary>
    /// Called once at start of game and subscribes methods to the events.
    /// </summary>
    void Start()
    {
		feedbackStream = gameObject.GetComponent<LSLFeedbackStream>();
        markerStream = gameObject.GetComponent<LSLMarkerStream>();
        textureController = gameObject.GetComponent<TextureColorController>();

        // Subscribe methods to events
        EventManager.instance.TriggerSessionStarted += OnSessionStarted;
        EventManager.instance.TriggerSessionFinished += OnSessionFinished;
        EventManager.instance.TriggerTrialStarted += OnTrialStarted;
        EventManager.instance.TriggerReference += OnReference;
        EventManager.instance.TriggerCue += OnCue;
        EventManager.instance.TriggerFeedback += OnFeedback;
        EventManager.instance.TriggerTrialEnd += OnTrialEnd;
        EventManager.instance.TriggerResetObjects += OnResetObjects;
        EventManager.instance.TriggerUpdateGlow += OnUpdateGlow;
        EventManager.instance.TriggerUpdateERDS += OnUpdateERDS;

        OnResetObjects();
    }

    /// <summary>
    /// Handles what happens at the start of the session.
    /// </summary>
    void OnSessionStarted()
    {
        markerStream.Write("Session_Start");
    }

    /// <summary>
    /// Handles what happens at the end of the session.
    /// </summary>
    void OnSessionFinished()
    {
        markerStream.Write("Session_End");
    }

    /// <summary>
    /// Handles what happens at the start of each trial.
    /// </summary>
    void OnTrialStarted(string condition)
    {
        markerStream.Write("Start_of_Trial_" + condition);
    }

    /// <summary>
    /// Handles what happens on reference time of each trial.
    /// </summary>
    void OnReference()
    {
        markerStream.Write("Reference");
        fixationCross.SetActive(true);
    }

    /// <summary>
    /// Handles what happens on cue time of each trial.
    /// </summary>
    void OnCue(uint condition)
    {
        markerStream.Write("Cue");
        if (condition == (uint)ScenarioController.AllConditions.LEFT_HAND)
            arrowLeft.SetActive(true);
        else if (condition == (uint)ScenarioController.AllConditions.RIGHT_HAND)
            arrowRight.SetActive(true);
    }

    /// <summary>
    /// Handles what happens on feedback time of each trial.
    /// </summary>
    void OnFeedback(uint condition)
    {
        if (!ScenarioController.instance.showFeedback)
            return;

        fixationCross.SetActive(false);

        markerStream.Write("Feedback");

        brain.SetActive(true);
        glow.SetActive(true);	

    }

    /// <summary>
    /// Handles what happens at the end of each trial.
    /// </summary>
    void OnTrialEnd()
    {
        markerStream.Write("End_of_Trial");
        
        OnResetObjects();
    }

    /// <summary>
    /// Hides all objects and sets the texture of the brain object to default values.
    /// </summary>
    public void OnResetObjects()
	{
        fixationCross.SetActive(false);
		arrowLeft.SetActive(false);
		arrowRight.SetActive(false);
		brain.SetActive(false);
        glow.SetActive(false);	

        textureController.ResetTexture();
	}

    /// <summary>
    /// Updates the glow colour and intensity of the brain object.
    /// </summary>
    void OnUpdateGlow(float distance, bool is_correct)
    {
        textureController.GlowIntensity(distance, is_correct);
    }

    /// <summary>
    /// Updates the colour of each region of interest of the brain object. 
    /// </summary>
    public void OnUpdateERDS(float[] values)
    {
        textureController.UpdateERDSValues(values);
    }
}
